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
import Zwave
import math
import osmosdr
import threading
import time


class top_block(gr.top_block):

    def __init__(self, channel=908.4e6, gain=40):
        gr.top_block.__init__(self, "Top Block")

        ##################################################
        # Parameters
        ##################################################
        self.channel = channel
        self.gain = gain

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 800000
        self.taps = taps = firdes.low_pass(1,samp_rate,150e3,50e3,firdes.WIN_HAMMING)
        self.seuil = seuil = -40

        ##################################################
        # Blocks
        ##################################################
        self.xmlrpc_server_0 = SimpleXMLRPCServer.SimpleXMLRPCServer(('localhost', 8080), allow_none=True)
        self.xmlrpc_server_0.register_instance(self)
        self.xmlrpc_server_0_thread = threading.Thread(target=self.xmlrpc_server_0.serve_forever)
        self.xmlrpc_server_0_thread.daemon = True
        self.xmlrpc_server_0_thread.start()
        self.osmosdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + '' )
        self.osmosdr_source_0.set_sample_rate(samp_rate)
        self.osmosdr_source_0.set_center_freq(channel + 200e3, 0)
        self.osmosdr_source_0.set_freq_corr(0, 0)
        self.osmosdr_source_0.set_dc_offset_mode(0, 0)
        self.osmosdr_source_0.set_iq_balance_mode(0, 0)
        self.osmosdr_source_0.set_gain_mode(False, 0)
        self.osmosdr_source_0.set_gain(gain, 0)
        self.osmosdr_source_0.set_if_gain(20, 0)
        self.osmosdr_source_0.set_bb_gain(20, 0)
        self.osmosdr_source_0.set_antenna('', 0)
        self.osmosdr_source_0.set_bandwidth(0, 0)

        self.low_pass_filter_0 = filter.fir_filter_fff(1, firdes.low_pass(
        	1, samp_rate, 40e3, 10e3, firdes.WIN_HAMMING, 6.76))
        self.freq_xlating_fir_filter_xxx_0 = filter.freq_xlating_fir_filter_ccc(1, (taps), -200e3, samp_rate)
        self.digital_clock_recovery_mm_xx_0 = digital.clock_recovery_mm_ff(20, 0.25*0.175*0.175, 0.5, 0.175, 0.005)
        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        self.blocks_socket_pdu_0_0 = blocks.socket_pdu("UDP_CLIENT", '127.0.0.1', '52002', 10000, False)
        self.blocks_message_debug_0 = blocks.message_debug()
        self.analog_simple_squelch_cc_0 = analog.simple_squelch_cc(seuil, 1)
        self.analog_quadrature_demod_cf_0 = analog.quadrature_demod_cf(2*(samp_rate)/(2*math.pi*20e3/8.0))
        self.Zwave_packet_sink_0 = Zwave.packet_sink()



        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.Zwave_packet_sink_0, 'out'), (self.blocks_message_debug_0, 'print_pdu'))
        self.msg_connect((self.Zwave_packet_sink_0, 'out'), (self.blocks_socket_pdu_0_0, 'pdus'))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.analog_simple_squelch_cc_0, 0), (self.analog_quadrature_demod_cf_0, 0))
        self.connect((self.digital_binary_slicer_fb_0, 0), (self.Zwave_packet_sink_0, 0))
        self.connect((self.digital_clock_recovery_mm_xx_0, 0), (self.digital_binary_slicer_fb_0, 0))
        self.connect((self.freq_xlating_fir_filter_xxx_0, 0), (self.analog_simple_squelch_cc_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.digital_clock_recovery_mm_xx_0, 0))
        self.connect((self.osmosdr_source_0, 0), (self.freq_xlating_fir_filter_xxx_0, 0))

    def get_channel(self):
        return self.channel

    def set_channel(self, channel):
        self.channel = channel
        self.osmosdr_source_0.set_center_freq(self.channel + 200e3, 0)

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain
        self.osmosdr_source_0.set_gain(self.gain, 0)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_taps(firdes.low_pass(1,self.samp_rate,150e3,50e3,firdes.WIN_HAMMING))
        self.osmosdr_source_0.set_sample_rate(self.samp_rate)
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, 40e3, 10e3, firdes.WIN_HAMMING, 6.76))
        self.analog_quadrature_demod_cf_0.set_gain(2*(self.samp_rate)/(2*math.pi*20e3/8.0))

    def get_taps(self):
        return self.taps

    def set_taps(self, taps):
        self.taps = taps
        self.freq_xlating_fir_filter_xxx_0.set_taps((self.taps))

    def get_seuil(self):
        return self.seuil

    def set_seuil(self, seuil):
        self.seuil = seuil
        self.analog_simple_squelch_cc_0.set_threshold(self.seuil)


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    parser.add_option(
        "", "--channel", dest="channel", type="eng_float", default=eng_notation.num_to_str(908.4e6),
        help="Set channel [default=%default]")
    parser.add_option(
        "-g", "--gain", dest="gain", type="eng_float", default=eng_notation.num_to_str(40),
        help="Set gain [default=%default]")
    return parser


def main(top_block_cls=top_block, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    tb = top_block_cls(channel=options.channel, gain=options.gain)
    tb.start()
    try:
        raw_input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
