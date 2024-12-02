"""
==========================================================================
OutputUnitRTL_test.py
==========================================================================
Test cases for OutputUnitRTL.

Author : Yanghui Ou, Cheng Tan
  Date : June 22, 2019
"""


from hypothesis import strategies as st
from pymtl3 import *
from pymtl3.datatypes import strategies as pst
# from .OutputUnitCL_test import OutputUnitCL_Tests as BaseTests
from ..OutputUnitRTL import OutputUnitRTL
from ...ocnlib.utils import run_sim
from ......lib.basic.val_rdy.queues import (BypassQueueRTL, NormalQueueRTL,
                                            PipeQueueRTL)
from ......lib.basic.val_rdy.SinkRTL import SinkRTL as TestSinkRTL
from ......lib.basic.val_rdy.SourceRTL import SourceRTL as TestSrcRTL

import hypothesis
import pytest


#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness(Component):

  def construct(s, MsgType, src_msgs, sink_msgs):

    s.src = TestSrcRTL(MsgType, src_msgs)
    s.dut = OutputUnitRTL(MsgType)
    s.sink = TestSinkRTL(MsgType, sink_msgs)

    # Connections
    s.src.send //= s.dut.recv
    s.dut.send //= s.sink.recv

  def done(s):
    return s.src.done() and s.sink.done()

  def line_trace(s):
    return "{}>{}>{}".format(
      s.src.line_trace(),
      s.dut.line_trace(),
      s.sink.line_trace()
    )

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

# class OutputUnitRTL_Tests(BaseTests):
class OutputUnitRTL_Tests():

  @classmethod
  def setup_class(cls):
    cls.TestHarness = TestHarness
    cls.qtypes = [NormalQueueRTL, PipeQueueRTL, BypassQueueRTL]

  def test_normal2_simple( s ):
    test_msgs = [ b16( 4 ), b16( 1 ), b16( 2 ), b16( 3 ) ]
    # arrival_time = [ 2, 3, 4, 5 ]
    th = s.TestHarness( Bits16, test_msgs, test_msgs )
    th.set_param( "top.sink.construct" )
    run_sim( th )

  def test_hypothesis( s ):
    @hypothesis.settings( deadline=None )
    @hypothesis.given(
      qsize     = st.integers(1, 16),
      dwid      = st.integers(1, 32),
      sink_init = st.integers(0, 20),
      qtype     = st.sampled_from( s.qtypes ),
      test_msgs = st.data(),
    )
    def actual_test( dwid, qsize, qtype, sink_init, test_msgs ):
      msgs = test_msgs.draw( st.lists( pst.bits(dwid), min_size=1, max_size=100 ) )
      th = s.TestHarness( mk_bits(dwid), msgs, msgs )
      th.set_param( "top.sink.construct", initial_delay=sink_init )
      th.set_param( "top.dut.construct", QueueType = qtype )
      th.set_param( "top.dut.queue.construct", num_entries=qsize )
      run_sim( th, max_cycles=5000 )
    actual_test()
