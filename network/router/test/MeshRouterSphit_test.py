import pytest

from pymtl import *
from network.router.MeshRouterSphit import MeshRouterSphit
from ocn_pclib.SinglePhitPacket import SinglePhitPacket
from pclib.test import TestSource, TestSink, mk_test_case_table
import copy

#=======================================================================
# Test Harness
#=======================================================================
class TestHarness( Model ):

  def __init__( s, router, pkt_type, pos_x, pos_y, src_msgs, 
                sink_msgs, src_delay, sink_delay, 
                dump_vcd=False, test_verilog=False ):
   
    # Constants 
    s.src_msgs    = src_msgs
    s.sink_msgs   = sink_msgs
    s.src_delay   = src_delay
    s.sink_delay  = sink_delay
    s.num_ports = 5
   
    s.src  = [ TestSource( pkt_type, s.src_msgs[i],  s.src_delay ) 
    		 	 	   for i in range( s.num_ports )]
    s.sink = [   TestSink( pkt_type, s.sink_msgs[i], s.sink_delay )
    		 		   for i in range( s.num_ports )]
    s.dut = router
    
    # Dump vcd and verilog translation
    if dump_vcd:
      s.dut.vcd_file = dump_vcd

    if test_verilog:
      s.dut = TranslationTool( s.dut )
    
    # Connections
    for i in range( s.num_ports ):
      s.connect( s.src[i].out, s.dut.in_[i]  )
      s.connect( s.dut.out[i], s.sink[i].in_ )

    s.connect( s.dut.pos_x, pos_x )
    s.connect( s.dut.pos_y, pos_y )
  
  def done( s ):
    done_flag = True
    for i in range( s.num_ports ):
      done_flag &= s.src[i].done and s.sink[i].done
    return done_flag

  # TODO: Implement line trace.
  def line_trace( s ):
    in_ = '|'.join( [ x.out.to_str( "%02s:(%1s,%1s)>(%1s,%1s)" % (
                                     x.out.msg.opaque, 
                                     x.out.msg.src_x, x.out.msg.src_y,
                                     x.out.msg.dst_x, x.out.msg.dst_y ) )
                      for x in s.src  ] )

    out = '|'.join( [ x.in_.to_str( "%02s:(%1s,%1s)>(%1s,%1s)" % (
                                     x.in_.msg.opaque, 
                                     x.in_.msg.src_x, x.in_.msg.src_y,
                                     x.in_.msg.dst_x, x.in_.msg.dst_y ) )
                      for x in s.sink ] )
    return in_ + '>' + s.dut.line_trace() + '>' + out

#=======================================================================
# Driver function  
#=======================================================================

def run_router_test( router, pkt_type, pos_x, pos_y, 
                     test_msgs, src_delay, sink_delay,
                     dump_vcd=False, test_verilog=False ):
  """
  A helper function that runs the tests for a given router.
  """
  max_cycles = 200

  src_msgs  = test_msgs[0]
  sink_msgs = test_msgs[1]
 
  # Instantiate and elaborate the test harness
  model = TestHarness( router, pkt_type, pos_x, pos_y, 
                       src_msgs, sink_msgs, src_delay, sink_delay,
                       dump_vcd, test_verilog )
  model.vdc_file = dump_vcd
  model.test_verilog = test_verilog
  model.elaborate()

  # Run simulation
  sim = SimulationTool( model )
  print ""
  print "="*72
  sim.reset()
  while not model.done() and sim.ncycles < max_cycles:
    sim.eval_combinational() 
    sim.print_line_trace()
    sim.cycle()

  # A few extra cycles to make waveform looks nicer
  sim.cycle()
  sim.cycle()
  sim.cycle()

  if not model.done():
    raise AssertionError( "Simulation did not complete in %d cylces!" 
                          % max_cycles )

#=======================================================================
# Helper stuff
#=======================================================================

base_pkt = SinglePhitPacket( 4, 4, 4, 4, 8, 32 )

def mk_pkt( base_pkt, src_x, src_y, dst_x, dst_y, opaque, payload ):
  pkt = copy.deepcopy( base_pkt ) 
  pkt.src_x   = src_x
  pkt.src_y   = src_y
  pkt.dst_x   = dst_x
  pkt.dst_y   = dst_y
  pkt.opaque  = opaque
  pkt.payload = payload
  return pkt

def mk_test_msgs( num_ports, base_pkt, msg_list ):
  """
  A helper function that makes a list of src/sink packets from the
  input messages.
  """
  src_msgs  = [ [] for _ in range( num_ports ) ]
  sink_msgs = [ [] for _ in range( num_ports ) ]
  
  for m in msg_list:
    tsrc, tsink, src_x, src_y, dst_x, dst_y, opaque, payload = \
    m[0], m[1],  m[2],  m[3],  m[4],  m[5],  m[6],   m[7]
    pkt = mk_pkt( base_pkt, src_x, src_y, dst_x, dst_y, opaque, payload ) 
    src_msgs [ tsrc].append( pkt )
    sink_msgs[tsink].append( pkt )

  return [ src_msgs, sink_msgs ]

def dimension_order_routing( dimension, pos_x, pos_y,
                             src_x, src_y, dest_x, dest_y ):
  tsrc  = 0
  tsink = 0
  north = 0
  south = 1
  west  = 2
  east  = 3
  inout = 4
  # determine source port
  if src_x == pos_x and src_y == pos_y:
    tsrc = inout

  elif dimension == 'y':
    if src_x == pos_x:
      if src_y < pos_y:
        tsrc = west
      else:
        tsrc = east
    elif src_x < pos_x:
      tsrc = north
    else:
      tsrc = west

  elif dimension == 'x':
    if src_y == pos_y:
      if src_x < pos_x:
        tsrc = north
      else:
        tsrc = south
    elif src_y > pos_y:
      tsrc = east
    else:
      tsrc = west
  else:
    raise AssertionError( "Invalid dimension input for DOR! " )
  # determine dest port
  if dest_x == pos_x and dest_y == pos_y:
    tsink = inout
  elif dimension == 'y':
    if dest_y > pos_y:
      tsink = east
    elif dest_y < pos_y:
      tsink = west
    elif dest_x > pos_x:
      tsink = south
    else:
      tsink = north
  elif dimension == 'x':
    if dest_x > pos_x:
      tsink = south
    elif dest_x < pos_x:
      tsink = north
    elif dest_y > pos_y:
      tsink = east
    else:
      tsink = west
  else:
    raise AssertionError( "Invalid dimension input for DOR! " )
  return (tsrc, tsink)

def compute_src_sink( pos_x, pos_y, dimension, msg_list ):
  """
  A helper function that computes the corresponding test src/sink
  based on the input packet and the router's position.
  """
  test_list = []
  tsrc  = 0
  tsink = 0

  for m in msg_list:
    if dimension.lower() != 'x' and dimension.lower() != 'y':  
      raise AssertionError ("<copmute_src_sink> Invalid routing dimension!")

    tsrc, tsink = dimension_order_routing( dimension, pos_x, pos_y,
                                           m[0], m[1], m[2], m[3] )
    print ("{},{} for {}:({},{}>({},{}))".format(tsrc, tsink, m[4], m[2], m[3], m[0], m[1]))
    test_list.append( (tsrc, tsink, m[0], m[1], m[2], m[3], m[4], m[5]) )
  return test_list

#=======================================================================
# Directed tests
#=======================================================================

def basic_msgs( pos_x, pos_y, dimension, pkt_type ):
  return mk_test_msgs( 5, pkt_type, 
      compute_src_sink( pos_x, pos_y, dimension, [
        # src_x src_y dst_x dst_y opaque payload
        ( 0,    0,    1,    1,    0,     0xcafebeef )
      ] ) )

#=======================================================================
# Test case table
#=======================================================================

test_case_table = mk_test_case_table( [
  (               "msg_func   dimension pkt_type  pos_x pos_y src_delay sink_delay" ),
  [ "dor_y_1pkt", basic_msgs, 'x',      base_pkt, 0,    0,    0,        0           ]
] )

#=======================================================================
# Run the tests
#=======================================================================

@pytest.mark.parametrize( **test_case_table )
def test_direct( test_params, dump_vcd, test_verilog ):
  msgs = test_params.msg_func( test_params.pos_x, test_params.pos_y,
                               test_params.dimension, test_params.pkt_type )
  run_router_test( MeshRouterSphit( 
                     test_params.pkt_type, test_params.dimension ),
  test_params.pkt_type, test_params.pos_x, test_params.pos_y, msgs,
  test_params.src_delay, test_params.sink_delay, dump_vcd, test_verilog )