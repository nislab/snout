#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: IEEE 802.15.4 Transmitter using OQPSK PHY
# GNU Radio version: 3.7.13.5
##################################################

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"

from PyQt4 import Qt
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.qtgui import Range, RangeWidget
from math import sin, pi
from optparse import OptionParser
import ieee802_15_4
import pmt
import sys
import time
from gnuradio import qtgui


class transmitter_OQPSK(gr.top_block, Qt.QWidget):

    def __init__(self, num_messages=1000000000, pad=0x00, preamble=0x000000a7, tx_gain=.75):
        gr.top_block.__init__(self, "IEEE 802.15.4 Transmitter using OQPSK PHY")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("IEEE 802.15.4 Transmitter using OQPSK PHY")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "transmitter_OQPSK")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())


        ##################################################
        # Parameters
        ##################################################
        self.num_messages = num_messages
        self.pad = pad
        self.preamble = preamble
        self.tx_gain = tx_gain

        ##################################################
        # Variables
        ##################################################
        self.ch = ch = 11
        self.samp_rate = samp_rate = 4000000
        self.freq = freq = 1000000 * (2400 + 5 * (ch - 10))

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_sink_0 = uhd.usrp_sink(
        	",".join(('', "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        	'pdu_length',
        )
        self.uhd_usrp_sink_0.set_samp_rate(4000000)
        self.uhd_usrp_sink_0.set_center_freq(freq, 0)
        self.uhd_usrp_sink_0.set_normalized_gain(tx_gain, 0)
        self.ieee802_15_4_rime_stack_0 = ieee802_15_4.rime_stack(([129]), ([131]), ([132]), ([23,42]))
        self.ieee802_15_4_mac_0 = ieee802_15_4.mac(True,0x8841,0,0x1aaa,0xffff,0x3344)
        self.ieee802_15_4_access_code_prefixer_0 = ieee802_15_4.access_code_prefixer(pad,preamble)
        self.digital_chunks_to_symbols_xx_0 = digital.chunks_to_symbols_bc(([(1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (1-1j), (-1+1j), (1+1j), (-1-1j), (-1-1j), (1+1j), (-1+1j), (-1+1j), (-1-1j), (1-1j), (-1-1j), (1-1j), (1+1j), (1-1j), (1+1j), (-1+1j), (1+1j), (-1-1j), (1-1j), (-1+1j), (-1+1j), (1-1j), (-1-1j), (-1-1j), (-1+1j), (1+1j), (-1+1j), (1+1j), (1-1j), (1+1j), (1-1j), (-1-1j)]), 16)
        self.digital_burst_shaper_xx_0 = digital.burst_shaper_cc((([])), 0, 4, False, "pdu_length")
        self._ch_range = Range(11, 26, 1, 11, 200)
        self._ch_win = RangeWidget(self._ch_range, self.set_ch, "ch", "counter_slider", float)
        self.top_grid_layout.addWidget(self._ch_win)
        self.blocks_vector_source_x_0 = blocks.vector_source_c([0, sin(pi/4), 1, sin(3*pi/4)], True, 1, [])
        self.blocks_tagged_stream_multiply_length_0 = blocks.tagged_stream_multiply_length(gr.sizeof_gr_complex*1, 'pdu_length', 128)
        self.blocks_tag_gate_0 = blocks.tag_gate(gr.sizeof_float * 1, False)
        self.blocks_tag_gate_0.set_single_key("")
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_gr_complex*1, 4)
        self.blocks_pdu_to_tagged_stream_0_0_0 = blocks.pdu_to_tagged_stream(blocks.byte_t, 'pdu_length')
        self.blocks_packed_to_unpacked_xx_0 = blocks.packed_to_unpacked_bb(4, gr.GR_LSB_FIRST)
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.blocks_message_strobe_0 = blocks.message_strobe(pmt.intern("Hello World!\n"), 1000)
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_float*1, 2)
        self.blocks_complex_to_float_0 = blocks.complex_to_float(1)



        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.blocks_message_strobe_0, 'strobe'), (self.ieee802_15_4_rime_stack_0, 'bcin'))
        self.msg_connect((self.ieee802_15_4_access_code_prefixer_0, 'out'), (self.blocks_pdu_to_tagged_stream_0_0_0, 'pdus'))
        self.msg_connect((self.ieee802_15_4_mac_0, 'pdu out'), (self.ieee802_15_4_access_code_prefixer_0, 'in'))
        self.msg_connect((self.ieee802_15_4_mac_0, 'app out'), (self.ieee802_15_4_rime_stack_0, 'fromMAC'))
        self.msg_connect((self.ieee802_15_4_rime_stack_0, 'toMAC'), (self.ieee802_15_4_mac_0, 'app in'))
        self.connect((self.blocks_complex_to_float_0, 1), (self.blocks_delay_0, 0))
        self.connect((self.blocks_complex_to_float_0, 0), (self.blocks_float_to_complex_0, 0))
        self.connect((self.blocks_delay_0, 0), (self.blocks_tag_gate_0, 0))
        self.connect((self.blocks_float_to_complex_0, 0), (self.uhd_usrp_sink_0, 0))
        self.connect((self.blocks_multiply_xx_0, 0), (self.blocks_tagged_stream_multiply_length_0, 0))
        self.connect((self.blocks_packed_to_unpacked_xx_0, 0), (self.digital_chunks_to_symbols_xx_0, 0))
        self.connect((self.blocks_pdu_to_tagged_stream_0_0_0, 0), (self.blocks_packed_to_unpacked_xx_0, 0))
        self.connect((self.blocks_repeat_0, 0), (self.blocks_multiply_xx_0, 1))
        self.connect((self.blocks_tag_gate_0, 0), (self.blocks_float_to_complex_0, 1))
        self.connect((self.blocks_tagged_stream_multiply_length_0, 0), (self.digital_burst_shaper_xx_0, 0))
        self.connect((self.blocks_vector_source_x_0, 0), (self.blocks_multiply_xx_0, 0))
        self.connect((self.digital_burst_shaper_xx_0, 0), (self.blocks_complex_to_float_0, 0))
        self.connect((self.digital_chunks_to_symbols_xx_0, 0), (self.blocks_repeat_0, 0))

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "transmitter_OQPSK")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_num_messages(self):
        return self.num_messages

    def set_num_messages(self, num_messages):
        self.num_messages = num_messages

    def get_pad(self):
        return self.pad

    def set_pad(self, pad):
        self.pad = pad

    def get_preamble(self):
        return self.preamble

    def set_preamble(self, preamble):
        self.preamble = preamble

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.uhd_usrp_sink_0.set_normalized_gain(self.tx_gain, 0)


    def get_ch(self):
        return self.ch

    def set_ch(self, ch):
        self.ch = ch
        self.set_freq(1000000 * (2400 + 5 * (self.ch - 10)))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.uhd_usrp_sink_0.set_center_freq(self.freq, 0)


def argument_parser():
    parser = OptionParser(usage="%prog: [options]", option_class=eng_option)
    parser.add_option(
        "-n", "--num-messages", dest="num_messages", type="intx", default=1000000000,
        help="Set num_messages [default=%default]")
    parser.add_option(
        "", "--pad", dest="pad", type="intx", default=0x00,
        help="Set pad [default=%default]")
    parser.add_option(
        "-p", "--preamble", dest="preamble", type="intx", default=0x000000a7,
        help="Set preamble [default=%default]")
    parser.add_option(
        "-g", "--tx-gain", dest="tx_gain", type="eng_float", default=eng_notation.num_to_str(.75),
        help="Set tx_gain [default=%default]")
    return parser


def main(top_block_cls=transmitter_OQPSK, options=None):
    if options is None:
        options, _ = argument_parser().parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable real-time scheduling."

    from distutils.version import StrictVersion
    if StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(num_messages=options.num_messages, pad=options.pad, preamble=options.preamble, tx_gain=options.tx_gain)
    tb.start()
    tb.show()

    def quitting():
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()


if __name__ == '__main__':
    main()
