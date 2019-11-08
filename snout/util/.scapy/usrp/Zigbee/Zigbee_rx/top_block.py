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
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from math import sin, pi
from optparse import OptionParser
import math
import time
import zigbee


class top_block(gr.top_block):

    def __init__(self, channel=11, channel_max=11, channel_min=11):
        gr.top_block.__init__(self, "Top Block")

        ##################################################
        # Parameters
        ##################################################
        self.channel = channel
        self.channel_max = channel_max
        self.channel_min = channel_min

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 4000000

        ##################################################
        # Blocks
        ##################################################
        self.zigbee_packet_sink_scapy_0 = zigbee.packet_sink_scapy(10)
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join(('', "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(1000000 * (2400 + 5 * (channel - 10)), 0)
        self.uhd_usrp_source_0.set_gain(40, 0)
        self.uhd_usrp_source_0.set_antenna('RX2', 0)
        self.uhd_usrp_source_0.set_auto_dc_offset(False, 0)
        self.uhd_usrp_source_0.set_auto_iq_balance(False, 0)
        self.single_pole_iir_filter_xx_0 = filter.single_pole_iir_filter_ff(0.00016, 1)
        self.digital_clock_recovery_mm_xx_0 = digital.clock_recovery_mm_ff(2, 0.000225, 0.5, 0.03, 0.0002)
        self.blocks_sub_xx_0 = blocks.sub_ff(1)
        self.blocks_socket_pdu_0_0_0 = blocks.socket_pdu("UDP_CLIENT", '127.0.0.1', '52002', 10000, False)
        self.blocks_message_debug_0 = blocks.message_debug()
        self.analog_quadrature_demod_cf_0 = analog.quadrature_demod_cf(1)



        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.zigbee_packet_sink_scapy_0, 'out'), (self.blocks_message_debug_0, 'print_pdu'))
        self.msg_connect((self.zigbee_packet_sink_scapy_0, 'out'), (self.blocks_socket_pdu_0_0_0, 'pdus'))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.blocks_sub_xx_0, 0))
        self.connect((self.analog_quadrature_demod_cf_0, 0), (self.single_pole_iir_filter_xx_0, 0))
        self.connect((self.blocks_sub_xx_0, 0), (self.digital_clock_recovery_mm_xx_0, 0))
        self.connect((self.digital_clock_recovery_mm_xx_0, 0), (self.zigbee_packet_sink_scapy_0, 0))
        self.connect((self.single_pole_iir_filter_xx_0, 0), (self.blocks_sub_xx_0, 1))
        self.connect((self.uhd_usrp_source_0, 0), (self.analog_quadrature_demod_cf_0, 0))

    def get_channel(self):
        return self.channel

    def set_channel(self, channel):
        self.channel = channel
        self.uhd_usrp_source_0.set_center_freq(1000000 * (2400 + 5 * (self.channel - 10)), 0)

    def get_channel_max(self):
        return self.channel_max

    def set_channel_max(self, channel_max):
        self.channel_max = channel_max

    def get_channel_min(self):
        return self.channel_min

    def set_channel_min(self, channel_min):
        self.channel_min = channel_min

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    parser.add_option(
        "-c", "--channel", dest="channel", type="intx", default=11,
        help="Set channel [default=%default]")
    return parser


def main(top_block_cls=top_block, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()

    tb = top_block_cls(channel=options.channel)
    tb.start()
    try:
        raw_input('Press Enter to quit: \n')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()
