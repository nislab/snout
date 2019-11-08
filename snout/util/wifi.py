import datetime
import logging
import os
import subprocess
import time

import click

import prettytable as pt
import scapy.layers.dot11 as dot11
import scapy.layers.gnuradio as gnuradio
import scapy.modules.gnuradio as gnu_scapy
from scapy.all import *
from snout.core.protocols import WIFI
from snout.core.radio import Scan
from snout.core.pcontroller import PController


class WifiScan(Scan):
    """Helps to perform a wifi scan.
    """

    def __init__(
        self,
        active=None,
        channels=None,
        display=True,
        env=None,
        filename=None,
        radio=None,
        packet_threshold=None,
        timeout=None,
        wireshark=False,
    ):
        super().__init__(
            active=active,
            channels=channels,
            display=display,
            env=env,
            filename=filename,
            packet_threshold=packet_threshold,
            protocol=WIFI,
            radio=radio,
            timeout=timeout,
            wireshark=wireshark,
        )
        self.logger = logging.getLogger(__name__)

        if not packet_threshold:
            # for scapy sniff, count=0 --> infinite number to sniff
            self.packet_threshold = 0

    def handle_packet(self, pkt):
        """See util/scan.py
        """
        try:
            pkt = scapy.layers.rftap.RFtap(pkt)
        except:
            pkt = dot11.Dot11(pkt)
        pkt.show()
        self.packets.append(pkt)
        # TODO Save RFTap layer too...doesn't read write in wireshark,
        # so just save the payload, which is the packet data without RFTap
        wrpcap(self.filename, pkt.payload, append=True)

    def check_stop(self, num_packets):
        """See util/scan.py
        """
        pass
