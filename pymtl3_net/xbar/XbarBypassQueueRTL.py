'''
==========================================================================
XbarBypassQueueRTL.py
==========================================================================
A crossbar that supports single-flit packet. The input is a bypass queue.

Author : Yanghui Ou, Cheng Tan
  Date : Dec 7, 2024
'''


from pymtl3 import *
from .XbarRouteUnitRTL import XbarRouteUnitRTL
from ..router.InputUnitRTL import InputUnitRTL
from ..router.OutputUnitRTL import OutputUnitRTL
from ..router.SwitchUnitRTL import SwitchUnitRTL
from ..router.SwitchUnitNullRTL import SwitchUnitNullRTL
from .....lib.basic.val_rdy.ifcs import RecvIfcRTL, SendIfcRTL
from .....lib.basic.val_rdy.queues import *


class XbarBypassQueueRTL(Component):

  def construct(s, PacketType, num_inports = 2, num_outports = 2,
                InputUnitType = InputUnitRTL,
                RouteUnitType = XbarRouteUnitRTL,
                SwitchUnitType = SwitchUnitRTL,
                OutputUnitType = OutputUnitRTL):

    # Local parameter

    s.num_inports = num_inports
    s.num_outports = num_outports

    # Special case for num_inports = 1
    if num_inports == 1: SwitchUnitType = SwitchUnitNullRTL

    # Interface

    s.recv = [RecvIfcRTL(PacketType) for _ in range(s.num_inports)]
    s.send = [SendIfcRTL(PacketType) for _ in range(s.num_outports)]

    # Components

    s.input_units = [InputUnitType(PacketType, BypassQueueRTL)
                     for _ in range(s.num_inports)]

    s.packet_on_input_units = [OutPort(PacketType) for _ in range(s.num_inports)]

    s.route_units = [RouteUnitType(PacketType, s.num_outports)
                     for i in range(s.num_inports)]

    s.switch_units = [SwitchUnitType(PacketType, s.num_inports)
                      for _ in range(s.num_outports)]

    s.output_units = [OutputUnitType(PacketType)
                      for _ in range(s.num_outports)]

    # Connections

    for i in range(s.num_inports):
      s.packet_on_input_units[i] //= s.input_units[i].send.msg

    for i in range(s.num_inports):
      s.recv[i] //= s.input_units[i].recv
      s.input_units[i].send //= s.route_units[i].recv

    for i in range(s.num_inports):
      for j in range(s.num_outports):
        s.route_units[i].send[j] //= s.switch_units[j].recv[i]

    for j in range(s.num_outports):
      s.switch_units[j].send //= s.output_units[j].recv
      s.output_units[j].send //= s.send[j]

  #-----------------------------------------------------------------------
  # Line trace
  #-----------------------------------------------------------------------

  def line_trace(s):
    in_trace = '|'.join([f'{ifc}' for ifc in s.recv])
    out_trace = '|'.join([f'{ifc}' for ifc in s.send])
    return f'{in_trace}(){out_trace}'
