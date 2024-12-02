"""
=========================================================================
SwitchUnitRTL_test.py
=========================================================================
Test for SwitchUnitRTL.

 Author : Yanghui Ou, Cheng Tan
   Date : June 22, 2019
"""


from pymtl3 import *
from ..SwitchUnitRTL import SwitchUnitRTL
from ...ocnlib.ifcs.packets import mk_generic_pkt
from ......lib.basic.val_rdy import SinkRTL as TestSinkRTL
from ......lib.basic.val_rdy import SourceRTL as TestSrcRTL


#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

def test_switch_unit_simple():
  dut = SwitchUnitRTL( Bits32, num_inports=5 )
  dut.elaborate()
  dut.apply( DefaultPassGroup(linetrace=True) )
  dut.sim_reset()

  dut.recv[0].val @= 1
  dut.recv[0].msg @= 0xfaceb00c
  dut.recv[1].val @= 1
  dut.recv[1].msg @= 0xdeadface
  dut.recv[4].val @= 1
  dut.recv[4].msg @= 0xbaadbeef
  dut.send.rdy@= 0
  dut.sim_eval_combinational()
  dut.sim_tick()

  for i in range( 3 ):
    dut.send.rdy @= 1
    dut.sim_eval_combinational()

    assert dut.send.rdy
    assert dut.send.msg in { b32(0xfaceb00c), b32(0xdeadface), b32(0xbaadbeef)  }
    dut.sim_tick()

