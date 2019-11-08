from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from math import sin, pi
from optparse import OptionParser
from transmitter_OQPSK import transmitter_OQPSK
from transmitter_OQPSK import argument_parser
from threading import Thread
import foo
import ieee802_15_4
import pmt
import time

# pseudo code
class FlowGraphWithExtras(transmitter_OQPSK):
    def __init(self, ch=11, num_messages=1000, pad=0x00, preamble=0x000000a7, tx_gain=.75):
        self.channel = ch
        self.num_messages = num_messages
        self.pad = pad
        self.preamble = preamble
        self.tx_gain = tx_gain
        print('Here1')
        super().__init__(self, self.channel, self.num_messages, self.pad, self.preamble, self.tx_gain)
        print('Here')
        # create new worker Thread with worker function self.additionalLogic()
        # start worker Thread
        # start flowgraph

    def additionalLogic(self, channel=11):
        time.sleep(5)
        #print('Switching to channel ' + str(channel))
        transmitter_OQPSK.__init__(self, channel, num_messages=1000, pad=0x00, preamble=0x000000a7, tx_gain=.75)
        self.wait()
        # do loopy stuff - change values every x seconds, etc.

def run_and_wait(ch):
    tb = transmitter_OQPSK(ch, num_messages=1000, pad=ch, preamble=0x000000a7, tx_gain=.75)
    tb.run()
    time.sleep(5)
    tb.stop()

def main(top_block_cls=FlowGraphWithExtras, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print("Error: failed to enable real-time scheduling.")

    for ch in range(11, 27):
        print('Switching to channel ' + str(ch))
        worker1 = Thread(target=run_and_wait, args=[ch])
        worker1.start()
        print(ch)
        time.sleep(10)

if __name__ == '__main__':
    main()