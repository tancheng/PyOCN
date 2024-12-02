"""
==========================================================================
OutputUnitCreditRTL.py
==========================================================================
An output unit with a credit based interface.

Author : Yanghui Ou
  Date : June 22, 2019
"""
from ..ocnlib.ifcs.CreditIfc import CreditSendIfcRTL, enrdy_to_str
from ..ocnlib.rtl import Counter
from pymtl3 import *
from .....lib.basic.val_rdy.ifcs import RecvIfcRTL


class OutputUnitCreditRTL( Component ):

  def construct( s, MsgType, vc=2, credit_line=2 ):
    assert vc > 1

    # Interface
    s.recv = RecvIfcRTL( MsgType )
    s.send = CreditSendIfcRTL( MsgType, vc )

    s.MsgType = MsgType
    s.vc      = vc

    # Loval types
    credit_type = mk_bits( clog2(credit_line+1) )

    s.credit = [ Counter( credit_type, credit_line ) for _ in range( vc ) ]

    s.recv.msg //= s.send.msg

    @update
    def up_credit_send():
      s.send.en  @= 0
      s.recv.rdy @= 0
      # NOTE: Here the recv.rdy depends on recv.val.
      #       Be careful about combinational loop.
      if s.recv.val:
        for i in range( vc ):
          if (i == s.recv.msg.vc_id) & (s.credit[i].count > 0):
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
