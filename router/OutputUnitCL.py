#=========================================================================
# OutputUnitCL.py
#=========================================================================
# Cycle level implementation of output unit.
#
# Author : Cheng Tan, Yanghui Ou
#   Date : Feb 28, 2019

from pymtl3 import *

class OutputUnitCL( Component ):

  def construct( s, PacketType, QueueType = None ):
    
    # Interface
    s.recv = NonBlockingCalleeIfc()
    s.send = NonBlockingCallerIfc()
    s.QueueType = QueueType

    # If no queue type is assigned
    if s.QueueType != None:
      # Component
      s.queue = QueueType( PacketType ) 

      s.connect( s.recv, s.queue.enq )
  
      @s.update
      def ou_up_send():
        if s.queue.deq.rdy() and s.send.rdy():
          s.send( s.queue.deq() )

    # No ouput queue
    else:
      s.connect( s.recv, s.send )

  def line_trace( s ):
    return ""