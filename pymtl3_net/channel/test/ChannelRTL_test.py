'''
=========================================================================
InputUnitRTLSourceSink_test.py
=========================================================================
Test for InputUnitRTL using Source and Sink

Author : Cheng Tan, Yanghui Ou
  Date : Feb 23, 2019
'''


from pymtl3 import *
from ..ChannelRTL import ChannelRTL
from ...ocnlib.utils import run_sim
from ......lib.basic.val_rdy.SinkRTL import SinkRTL as TestSinkRTL
from ......lib.basic.val_rdy.SourceRTL import SourceRTL as TestSrcRTL
from ......lib.basic.val_rdy.queues import NormalQueueRTL
import pytest


#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness(Component):

  def construct(s, MsgType, src_msgs, sink_msgs):

    s.src = TestSrcRTL(MsgType, src_msgs)
    s.sink = TestSinkRTL(MsgType, sink_msgs)
    s.dut = ChannelRTL(MsgType)

    # Connections
    s.src.send //= s.dut.recv
    s.dut.send //= s.sink.recv

  def done(s):
    return s.src.done() and s.sink.done()

  def line_trace(s):
    return s.src.line_trace() + "-> | " + \
           s.dut.line_trace() + " | -> " + \
           s.sink.line_trace()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

test_msgs = [b16(4), b16(1), b16(2), b16(3)]

def test_passthrough():
  th = TestHarness(Bits16, test_msgs, test_msgs)
  run_sim(th)

def test_normal2_simple():
  th = TestHarness(Bits16, test_msgs, test_msgs)
  th.set_param("top.dut.construct", latency= 2)
  run_sim(th)

