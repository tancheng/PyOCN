"""
==========================================================================
InputUnitCreditRTL.py
==========================================================================
An input unit with a credit based interface.

Author : Yanghui Ou
  Date : June 22, 2019
"""


from pymtl3 import *
from pymtl3.stdlib.primitive.arbiters import RoundRobinArbiterEn
from pymtl3.stdlib.primitive.encoders import Encoder
from ..ocnlib.ifcs.CreditIfc import CreditRecvIfcRTL
from .....lib.basic.val_rdy.ifcs import SendIfcRTL
from .....lib.basic.val_rdy.queues import NormalQueueRTL


class InputUnitCreditRTL( Component ):

  def construct( s, PacketType, QueueType = NormalQueueRTL,
                 vc=2, credit_line=2 ):

    # Local paramters
    s.vc = vc

    # Interface
    # FIXME: Implement ISLIP so that only one send interface is needed
    s.recv = CreditRecvIfcRTL( PacketType, vc=vc )
    s.send = [ SendIfcRTL( PacketType ) for _ in range( vc ) ]

    s.buffers = [ QueueType( PacketType, num_entries=credit_line )
                  for _ in range( vc ) ]

    for i in range( vc ):
      s.buffers[i].recv.msg //= s.recv.msg
      s.buffers[i].send     //= s.send[i]
      s.recv.yum[i]         //= lambda: s.send[i].val & s.send[i].rdy

    @update
    def up_enq():
      if s.recv.en:
        for i in range( vc ):
          s.buffers[i].recv.val @= ( s.recv.msg.vc_id == i )
      else:
        for i in range( vc ):
          s.buffers[i].recv.val @= 0

  def line_trace( s ):
    return "{}({}){}".format(
      s.recv,
      ",".join([ str(s.buffers[i].count) for i in range( s.vc ) ]),
      "|".join([ str(s.send[i]) for i in range( s.vc ) ]),
    )
