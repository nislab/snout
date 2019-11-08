#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Top Block
# GNU Radio version: 3.7.13.5
##################################################

from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from math import sin, pi
from optparse import OptionParser
import SimpleXMLRPCServer
import epy_block_0
import ieee802_15_4
import math
import osmosdr
import rftap
import threading
import time


class top_block(gr.top_block):

    def __init__(self, channel=26):
        gr.top_block.__init__(self, "Top Block")

        ##################################################
        # Parameters
        ##################################################
        self.channel = channel

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 4000000

        ##################################################
        # Blocks
        ##################################################
        self.xmlrpc_server_0 = SimpleXMLRPCServer.SimpleXMLRPCServer(('localhost', 8080), allow_none=True)
        self.xmlrpc_server_0.register_instance(self)
        self.xmlrpc_server_0_thread = threading.Thread(target=self.xmlrpc_server_0.serve_forever)
        self.xmlrpc_server_0_thread.daemon = True
        self.xmlrpc_server_0_thread.start()
        self.single_pole_iir_filter_xx_0 = filter.single_pole_iir_filter_ff(0.00016, 1)
        self.rftap_rftap_encap_0 = rftap.rftap_encap(2, 195, '')
        self.osmosdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + '' )
        self.osmosdr_source_0.set_sample_rate(samp_rate)
        self.osmosdr_source_0.set_center_freq(1000000 * (2400 + 5 * (channel - 10)), 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(False, 0)
        self.osmosdr_source_0.set_gain(10, 0)
        self.osmosdr_source_0.set_if_gain(20, 0)
        self.osmosdr_source_0.set_bb_gain(20, 0)
        self.osmosdr_source_0.set_antenna('', 0)
        self.osmosdr_source_0.set_bandwidth(0, 0)

        self.ieee802_15_4_packet_sink_0 = ieee802_15_4.packet_sink(10)
        self.epy_block_0 = epy_block_0.blk()
        self.digital_clock_recovery_mm_xx_0 = digital.clock_recovery_mm_ff(2, 0.000225, 0.5, 0.03, 0.0002)
        self.blocks_sub_xx_0 = blocks.sub_ff(1)
        self.blocks_socket_pdu_0_0_0 = blocks.socket_pdu("UDP_CLIENT", '127.0.0.1', '52002', 10000, False)
        self.blocks_message_debug_0 = blocks.message_debug()
        self.analog_quadrature_demod_cf_0 = analog.quadrature_demod_cf(1)



        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.epy_block_0, 'out'), (self.rftap_rftap_encap_0, 'in'))
        self.msg_connect((self.ieee802_15_4_packet_sink_0, 'out'), (self.epy_block_0, 'in'))
        self.msg_connect((self.rftap_rftap_encap_0, 'out'), (self.blocks_message_debug_0, 'print_pdu'))
        self.msg_connect((self.rftap_rftap_encap_0, 'out'), (self.blocks_socket_pdu_0_0_0, 'pdus'))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.blocks_sub_xx_0, 0))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.single_pole_iir_filter_xx_0, 0))
        self.connect((self.blocks_sub_xx_0, 0), (self.digital_clock_recovery_mm_xx_0, 0))
        self.connect((self.digital_clock_recovery_mm_xx_0, 0), (self.ieee802_15_4_packet_sink_0, 0))
        self.connect((self.osmosdr_source_0, 0), (self.analog_quadrature_demod_cf_0, 0))
        self.connect((self.single_pole_iir_filter_xx_0, 0), (self.blocks_sub_xx_0, 1))

    def get_channel(self):
        return self.channel

    def set_channel(self, channel):
        self.channel = channel
        self.osmosdr_source_0.set_center_freq(1000000 * (2400 + 5 * (self.channel - 10)), 0)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.osmosdr_source_0.set_sample_rate(self.samp_rate)


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    parser.add_option(
        "-c", "--channel", dest="channel", type="intx", default=26,
        help="Set channel [default=%default]")
    return parser


def main(top_block_cls=top_block, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    tb = top_block_cls(channel=options.channel)
    tb.start()
    try:
        raw_input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
