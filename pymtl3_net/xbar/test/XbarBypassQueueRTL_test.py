'''
==========================================================================
XbarBypassQueueRTL_test.py
==========================================================================
Unit tests for XbarBypassQueueRTL.

Author : Yanghui Ou, Cheng Tan
  Date : Dec 7, 2024
'''

from pymtl3 import *
from pymtl3.stdlib.test_utils import mk_test_case_table
from ..XbarBypassQueueRTL import XbarBypassQueueRTL
from ...ocnlib.ifcs.packets import mk_generic_pkt, mk_xbar_pkt
from ...ocnlib.utils import run_sim
from ...ocnlib.test.stream_sinks import NetSinkRTL as TestSink
from ......lib.basic.val_rdy.SourceRTL import SourceRTL as TestSource
import pytest


#-------------------------------------------------------------------------
# Constants
#-------------------------------------------------------------------------

opaque_nbits  = 8
payload_nbits = 32

#-------------------------------------------------------------------------
# test case: sanity check
#-------------------------------------------------------------------------

def test_sanity():
  PktT = mk_generic_pkt(nrouters=4, opaque_nbits=8, vc=0, payload_nbits=32)
  dut = XbarBypassQueueRTL(PktT, 2, 2)
  dut.elaborate()
  dut.apply(DefaultPassGroup())
  dut.sim_reset()
  dut.sim_tick()
  dut.sim_tick()

#-------------------------------------------------------------------------
# arrange_src_sink_pkts
#-------------------------------------------------------------------------

def arrange_src_sink_pkts(num_inports, num_outports, pkt_lst):
  src_pkts = [[] for _ in range(num_inports)]
  sink_pkts = [[] for _ in range(num_outports)]

  for pkt in pkt_lst:
    src = pkt.src.uint()
    dst = pkt.dst.uint()
    src_pkts[src].append(pkt)
    sink_pkts[dst].append(pkt)

  return src_pkts, sink_pkts

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness(Component):

  def construct(s, num_inports, num_outports, pkts):
    src_pkts, sink_pkts = \
      arrange_src_sink_pkts(num_inports, num_outports, pkts)

    PktT = mk_xbar_pkt(num_inports, num_outports, opaque_nbits, payload_nbits)
    s.src = [TestSource(PktT, src_pkts[i]) for i in range(num_inports)]
    s.dut = XbarBypassQueueRTL(PktT, num_inports, num_outports)
    s.sink = [TestSink(PktT, sink_pkts[i]) for i in range(num_outports)]

    for i in range(num_inports):
      s.src[i].send //= s.dut.recv[i]

    for i in range(num_outports):
      s.dut.send[i] //= s.sink[i].recv

  def done(s):
    src_done = True
    sink_done = True
    for m in s.src:
      src_done &= m.done()
    for m in s.sink:
      sink_done &= m.done()
    return src_done and sink_done

  def line_trace(s):
    return s.dut.line_trace()

#-------------------------------------------------------------------------
# test case: basic
#-------------------------------------------------------------------------

def basic_pkts(n_in, n_out):
  Pkt = mk_xbar_pkt(n_in, n_out, opaque_nbits, payload_nbits)
  return [
    Pkt(0, 0, 0x01, 0xfaceb000),
    Pkt(1, 0, 0x01, 0xfaceb001),
    Pkt(1, 1, 0x01, 0xfaceb002),
    Pkt(1, 1, 0x01, 0xfaceb003),
  ]

#-------------------------------------------------------------------------
# test case table
#-------------------------------------------------------------------------

test_cases = [
  (            'msg_func   n_in n_out init intv'),
  ['basic2x2', basic_pkts, 2,   2,    0,   0    ],
]

test_case_table = mk_test_case_table(test_cases)

#-------------------------------------------------------------------------
# test driver
#-------------------------------------------------------------------------

@pytest.mark.parametrize(**test_case_table)
def test_sflit_xbar(test_params, cmdline_opts):
  pkts = test_params.msg_func(test_params.n_in, test_params.n_out)
  th = TestHarness(test_params.n_in, test_params.n_out, pkts)
  th.set_param('top.sink*.construct',
    initial_delay = test_params.init,
    interval_delay = test_params.intv,
  )
  run_sim(th, cmdline_opts)
