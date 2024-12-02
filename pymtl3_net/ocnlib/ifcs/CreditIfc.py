"""
==========================================================================
 CreditIfc.py
==========================================================================
Credit based interfaces.

Author : Yanghui Ou
  Date : June 10, 2019
"""


from pymtl3 import *
from pymtl3.stdlib.primitive import Encoder
from pymtl3.stdlib.primitive.arbiters import RoundRobinArbiterEn
from ...ocnlib.rtl import Counter
from ......lib.basic.val_rdy.ifcs import RecvIfcRTL, SendIfcRTL
from ......lib.basic.val_rdy.queues import BypassQueueRTL


def enrdy_to_str( msg, en, rdy, trace_len=15 ):
    if     en  and not rdy: return "X".ljust( trace_len )
    if             not rdy: return "#".ljust( trace_len )
    if not en  and     rdy: return " ".ljust( trace_len )
    return f"{msg}".ljust( trace_len ) # en and rdy

#-------------------------------------------------------------------------
# RTL interfaces
#-------------------------------------------------------------------------

class CreditRecvIfcRTL( Interface ):

  def construct( s, MsgType, vc=1 ):
    assert vc > 1, "We only support multiple virtual channels!"

    s.en  = InPort ()
    s.msg = InPort ( MsgType )
    s.yum = [ OutPort() for i in range( vc ) ]

    s.MsgType = MsgType
    s.vc    = vc

  def __str__( s ):
    try:
      trace_len = s.trace_len
    except AttributeError:
      s.trace_len = len( str(s.MsgType()) )
      trace_len = s.trace_len
    return "{}:{}".format(
      enrdy_to_str( s.msg, s.en, True, s.trace_len ),
      "".join( [ "$" if x else '.' for x in s.yum ] )
    )

class CreditSendIfcRTL( Interface ):

  def construct( s, MsgType, vc=1 ):
    assert vc > 1, "We only support multiple virtual channels!"

    s.en  = OutPort()
    s.msg = OutPort( MsgType )
    s.yum = [ InPort() for _ in range( vc ) ]

    s.MsgType = MsgType
    s.vc      = vc

  def __str__( s ):
    try:
      trace_len = s.trace_len
    except AttributeError:
      s.trace_len = len( str(s.MsgType()) )
      trace_len = s.trace_len
    return "{}:{}".format(
      enrdy_to_str( s.msg, s.en, True, s.trace_len ),
      "".join( [ "$" if s.yum[i] else '.' for i in range(s.vc) ] )
    )

#-------------------------------------------------------------------------
# CL interfaces
#-------------------------------------------------------------------------

class CreditSendIfcCL( Interface ):

  def construct( s, MsgType, vc=1 ):
    assert vc > 1, "We only support multiple virtual channels!"

    s.send_msg    = CallerPort( MsgType )
    s.recv_credit = [ CalleePort() for _ in range( vc ) ]

    s.MsgType = MsgType
    s.vc      = vc

  def __str__( s ):
    return ""

class CreditRecvIfcCL( Interface ):

  def construct( s, MsgType, vc=1 ):
    assert vc > 1, "We only support multiple virtual channels!"

    s.recv_msg    = CalleePort( MsgType )
    s.send_credit = [ CallerPort() for _ in range( vc ) ]

    s.MsgType = MsgType
    s.vc    = vc

  def __str__( s ):
    return ""

#-------------------------------------------------------------------------
# CreditIfc adapters
#-------------------------------------------------------------------------

class RecvRTL2CreditSendRTL( Component ):

  def construct( s, MsgType, vc=2, credit_line=1 ):
    assert vc > 1

    # Interface

    s.recv = RecvIfcRTL( MsgType )
    s.send = CreditSendIfcRTL( MsgType, vc )

    s.MsgType = MsgType
    s.vc    = vc

    # Components

    CreditType = mk_bits( clog2(credit_line+1) )

    # FIXME: use multiple buffers to avoid deadlock.
    # s.buffer = BypassQueueRTL( MsgType, num_entries=1 )
    s.credit = [ Counter( CreditType, credit_line ) for _ in range( vc ) ]

    # s.recv           //=  s.buffer.enq
    # s.buffer.deq.ret //=  s.send.msg
    s.recv.msg //= s.send.msg

    @update
    def up_credit_send():
      s.send.en  @= 0
      s.recv.rdy @= 0
      # NOTE: recv.rdy depends on recv.val.
      #       Be careful about combinationl loop.
      if s.recv.val:
        for i in range( vc ):
          if ( i == s.recv.msg.vc_id ) & ( s.credit[i].count > 0 ):
            s.send.en  @= 1
            s.recv.rdy @= 1

    @update
    def up_counter_decr():
      for i in range( vc ):
        s.credit[i].decr @= s.send.en & ( i == s.send.msg.vc_id )

    for i in range( vc ):
      s.credit[i].incr       //= s.send.yum[i]
      s.credit[i].load       //= 0
      s.credit[i].load_value //= 0

  def line_trace( s ):
    return "{}({}){}".format(
      s.recv,
      ",".join( [ str(s.credit[i].count) for i in range(s.vc) ] ),
      s.send,
    )

class CreditRecvRTL2SendRTL( Component ):

  def construct( s, MsgType, vc=2, credit_line=1, QType=BypassQueueRTL ):
    assert vc > 1

    # Interface

    s.recv = CreditRecvIfcRTL( MsgType, vc )
    s.send = SendIfcRTL( MsgType )

    s.MsgType = MsgType
    s.vc      = vc

    # Components

    CreditType = mk_bits( clog2(credit_line+1) )

    s.buffers = [ QType( MsgType, num_entries=credit_line )
                  for _ in range( vc ) ]
    s.arbiter = RoundRobinArbiterEn( nreqs=vc )
    s.encoder = Encoder( in_nbits=vc, out_nbits=clog2(vc) )

    for i in range( vc ):
      s.buffers[i].recv.msg //= s.recv.msg
      s.buffers[i].send.val //= s.arbiter.reqs[i]
    s.arbiter.grants //= s.encoder.in_
    s.arbiter.en     //= s.send.val

    @update
    def up_enq():
      if s.recv.en:
        for i in range( vc ):
          s.buffers[i].recv.val @= ( s.recv.msg.vc_id == i )
      else:
        for i in range( vc ):
          s.buffers[i].recv.val @= 0

    # TODO: add some assertions to make sure val/rdy are both high
    #       when they should.
    @update
    def up_deq_and_send():
      for i in range( vc ):
        s.buffers[i].send.rdy @= 0

      s.send.msg @= s.buffers[ s.encoder.out ].send.msg

      if s.arbiter.grants > 0:
        s.send.val @= 1
        s.buffers[ s.encoder.out ].send.rdy @= s.send.rdy
      else:
        s.send.val @= 0

    @update
    def up_yummy():
      for i in range( vc ):
        s.recv.yum[i] @= s.buffers[i].send.val & s.buffers[i].send.rdy

  def line_trace( s ):
    return "{}(){}".format( s.recv, s.send )
