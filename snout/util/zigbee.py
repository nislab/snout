import ast
import datetime
import logging
import os
import subprocess
import time

import click
import pyshark

import scapy.layers.dot15d4 as dot15d4
import scapy.layers.gnuradio as gnuradio
import scapy.layers.rftap as rftap
import scapy.layers.zigbee as zigbee
import scapy.modules.gnuradio as gnu_scapy
from prettytable import PrettyTable
import scapy.all as scapy
from snout.core.protocols import ZIGBEE
from snout.core.radio import Scan, Transmission
from snout.core.config import Config as cfg
from snout.util.iot_click import iot_click
from snout.core.pcontroller import PController
from snout.util.touchlink_lib import Transaction


class ZigbeeScan(Scan):
    """Helps to perform a zigbee scan.
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
            protocol=ZIGBEE,
            radio=radio,
            timeout=timeout,
            wireshark=wireshark,
        )
        self.logger = logging.getLogger(__name__)
        if not packet_threshold:
            # for scapy sniff, count=0 --> infinite number to sniff
            self.packet_threshold = 0
        self.tl = Transaction() if active else None
        self.zll_responses = list()

    def run(self):
        """Runs an active scan if self.active, otherwise calls the inherited
        scan class' run method
        """
        if self.active:  # active scan for zll devices
            print('Actively scanning for ZLL devices...')
            self.zll_active_run()
            # self.send_scan_recv()
        else:
            super().run()

    def zll_active_run(self):
        """Runs a zll_active scan
        TODO: Make a more general active scan method
        """
        if not self.radio.full_duplex:
            print('A full duplex radio is required to scan actively')
            return
        while 1:
            try:
                self.tl.refresh_inter_pan_transaction_id()
                scan_request = self.tl.create_scan_request()
                send_pkts = list()
                if self.timeout:
                    send_pkts = [scan_request]*(int(self.timeout / .25))
                elif self.packet_threshold:
                    send_pkts = [scan_request]*self.packet_threshold
                if not send_pkts:
                    send_pkts = [scan_request]
                self.radio.switch_mode('Zigbee', 'rf')
                for ch in self.channels:
                    print(f"\nActively scanning on channel {ch}")
                    self.radio.set_channel(ch)
                    self.radio.srradio(
                        send_pkts,
                        radio=self.radio,
                        prn=self.handle_zll_packet,
                        wait_times=.25,
                        env=self.env,
                        params={'tx_gain': 100}
                    )
                if self.timeout or self.packet_threshold:
                    break
                else:
                    # continue indefinitely if no timeout and packet_threshold = 0 (infinite)
                    pass
            except ConnectionRefusedError:
                # don't raise since any keyboard interrupt with a XMLRPC dependent flow graph will throw this on a keyboard interrupt
                print('Socket ConnectionRefusedError')
                break
            except (KeyboardInterrupt, click.Abort):
                break  # still conclude
        self.zll_conclude()

    def zll_conclude(self):
        """Concludes a zll active scan by printing out general information
        and vulnerable devices
        TODO: Make a more general active scan conclude
        """
        self.radio.close_socket()
        if self.zll_responses:
            click.secho('\nVulnerable ZLL Devices:\n', fg='red')
            response_table = PrettyTable()
            response_table.field_names = [
                '#', 'Channel', 'Qual', 'Pan ID', 'Src Address']
            for ii in range(len(self.zll_responses)):
                response_table.add_row(
                    [
                        ii + 1,
                        self.zll_responses[ii]["channel"],
                        self.zll_responses[ii]["qual"],
                        self.zll_responses[ii]['pkt'].sprintf(
                            "%Dot15d4Data.src_panid%"
                        ),
                        self.zll_responses[ii]['pkt'].sprintf(
                            "%Dot15d4Data.src_addr%"
                        ),
                    ]
                )
            print(response_table)
            if self.wireshark:
                self.open_wireshark()
        else:
            click.secho('\nNo Vulnerable ZLL Devices Found\n', fg='cyan')
        log_table = PrettyTable()
        log_table.field_names = ['Log Type', 'Value']
        log_table.add_row(
            ['Gnuradio Stdout:', gnu_scapy.output()['stdout'].name]
        )
        log_table.add_row(
            ['Gnuradio Stderr:', gnu_scapy.output()['stderr'].name]
        )
        log_table.add_row(['File Dump:', self.filename])
        print("")
        print(log_table)

    def handle_zll_packet(self, pkt, channel=None, tx=False):
        """Handles ZLL packets during an active scan
        """
        if tx:
            print("Sent ZLL Scan Request Packet")
            self.packets.append(pkt)
            scapy.wrpcap(self.filename, pkt, append=True)
            return  # only process received responses, not the transmitted scan request
        pkt = rftap.RFtap(pkt)
        if pkt.haslayer(zigbee.ZLLScanResponse) and \
                self.tl.scan_request.inter_pan_transaction_id \
                == pkt.inter_pan_transaction_id:
            # check if duplicate response
            duplicate = False
            for r in self.zll_responses:
                if r['pkt'].src_addr == pkt.src_addr and \
                        r['pkt'].response_id == pkt.response_id:
                    duplicate = True
                    break
            if not duplicate:
                self.packets.append(pkt)
                pkt.show()
                print(
                    "Received ZLL Scan Response at {timestamp}: {summary}".format(
                        timestamp=pkt.time,
                        summary=pkt.payload.summary(),
                    )
                )
                self.zll_responses.append(
                    {
                        'pkt': pkt.payload,  # don't include rftap
                        'qual': pkt.qual,
                        'channel': self.radio.current_channel,
                    }
                )
        scapy.wrpcap(self.filename, pkt.payload, append=True)

    def handle_packet(self, pkt):
        """See util/scan.py
        """
        pkt = rftap.RFtap(pkt)
        pkt.show()
        self.packets.append(pkt)
        # TODO Save RFTap layer too...doesn't read write in wireshark,
        # so just save the payload, which is the packet data without RFTap
        scapy.wrpcap(self.filename, pkt.payload, append=True)

    def check_stop(self, pkt):
        """See util/scan.py
        """
        return (
            False
        )  # scapy handles all the stopping that we need to do for now, can add more options later


class ZigbeeTransmission(Transmission):
    """Handles Zigbee Transmissions
    TODO: Make a more general transmission class, like in the util/scan.py 
            module, which is in place for scans
    """

    def __init__(
        self, **kwargs
        #automatic=None,
    ):
        super().__init__(**kwargs)
        self.ans_packets = []
        self.fuzz = False
        self.preamble_max = kwargs.pop('preamble_max', [])
        self.preamble_min = kwargs.pop('preamble_min', [])
        self.single_replay_length = len(self.send_pkts)
        self.unans_packets = []

    def prompt_raw_bytes(self):
        """Prompts the user for raw bytes and tries to evaluate the raw input
        as a Dot15d4FCS packet and append it to self.send_pkts
        """
        iot_click.print("Enter in packet bytes in any of the possible forms:")
        iot_click.print("  Byte String: \\x00\\xff\\x0a\\x04")
        iot_click.print("  Space-Delimited Hex: 00 FF 0A 04")
        iot_click.print("  Comma-Delimited Hex: 00,FF,0A,04")
        while True:
            while True:
                p_bytes = iot_click.prompt("Enter packet bytes")
                p_bytes = self.evaluate_input_bytes(p_bytes)
                if p_bytes is not None:  # returned a valid evaluation
                    break
            packet = gnuradio.GnuradioPacket() / dot15d4.Dot15d4FCS(p_bytes)
            packet.show()
            self.send_pkts.append(packet)
            if not iot_click.confirm("Do you want to enter in another packet?"):
                break

    def prompt_pcap(self):
        """Prompts the user for a pcap file and prints out a short summary of each
        packet in the PCAP file. The user can then choose which packets they want
        to send with the call to  self.choose_indexes
        """
        while True:
            file_path = iot_click.prompt(
                "Pcap file path", type=click.Path(exists=True))
            try:
                pcap_pkts = [
                    pkt for pkt in scapy.rdpcap(file_path)
                ]  # convert to normal list instead of plist
                break
            except (IsADirectoryError, scapy.scapy.error.Scapy_Exception):
                print("Invalid Pcap file!")
        for ii in range(len(pcap_pkts)):
            iot_click.print(
                "{index} : {timestamp:.6f} : {summary}".format(
                    index=ii,
                    timestamp=pcap_pkts[ii].time,
                    summary=pcap_pkts[ii].summary(),
                )
            )
        self.send_pkts = self.choose_indexes(pcap_pkts)

    def prompt_replay(self):
        """Prompts the user to start a scan. Once the scan completes,
        if packets were received then the user can choose which packets
        out of the received that they want to send.
        """
        timeout = -1
        while timeout < 0:
            timeout = iot_click.prompt(
                "How long would you like to scan for (s)", type=click.INT
            )
        num = -1
        while num < 0:
            num = iot_click.prompt(
                "How many packets would you like to stop scanning at? (leave empty to disable)",
                type=click.INT,
                default=-1,
                show_default=False,
            )
            if num == -1:
                num = None
                break
        scan = ZigbeeScan(
            channels=self.channels,
            display=False,
            env=self.env,
            radio=self.radio,
            packet_threshold=num,
            timeout=timeout,
        )
        scan.run()
        if len(scan.packets) == 0:
            self.send_pkts = []
        for ii in range(len(scan.packets)):
            print(
                "{index} : {timestamp:.6f} : {summary}".format(
                    index=ii,
                    timestamp=scan.packets[ii].time,
                    summary=scan.packets[ii].summary(),
                )
            )
        self.send_pkts = [
            gnuradio.GnuradioPacket() / dot15d4.Dot15d4FCS(bytes(pkt))
            for pkt in self.choose_indexes(scan.packets, click_override=False)
        ]

    def prompt_modify_sequence(self):
        """Prompts the user to modify the sequence number, with several different
        options.
        TODO: use scapy's built in seqnum...will improve speed + readability
        """
        if not iot_click.confirm("Modify the sequence number?"):
            return
        iot_click.print(
            "\nChoose How you would like to modify the sequence number:")
        iot_click.print("  0: Increase by 1 for each packet")
        iot_click.print("  1: Increase by 1 for each transmission replay")
        iot_click.print("  2: Manually change, one packet at a time")
        iot_click.print(
            "  3: Manually change, one transmission replay at a time")
        modify_type = iot_click.prompt(
            "Your choice", type=click.IntRange(0, 3))
        if modify_type == 0 or modify_type == 1:
            increase_type = "packet" if modify_type == 0 else "transmission replay"
            if iot_click.confirm(
                "Increase the sequence number of the first {}?".format(
                    increase_type)
            ):
                seq_add = 1
            else:
                seq_add = 0
        # Modify as a dot154 packet and then convert back to GnuradioPacket after modifications
        self.send_pkts = [
            pkt for pkt in gnu_scapy.strip_gnuradio_layer(self.send_pkts)
        ]  # strip gnuradio and FCS layer
        if modify_type == 0 or modify_type == 2:
            for ii in range(0, len(self.send_pkts)):
                packet_bytes = bytearray(bytes(self.send_pkts[ii]))
                while True:
                    try:
                        if modify_type == 0:
                            seq_new = packet_bytes[2] + seq_add
                            if seq_new > 255:
                                seq_new %= 255
                            packet_bytes[2] = seq_new
                            seq_add += 1
                        else:
                            iot_click.print(
                                "\nPacket: {}".format(
                                    self.send_pkts[ii].summary())
                            )
                            iot_click.print(
                                "\nCurrent sequence number: {}".format(
                                    packet_bytes[2])
                            )
                            packet_bytes[2] = iot_click.prompt(
                                "New sequence number", type=click.IntRange(0, 255)
                            )
                        break
                    except ValueError:
                        print("Invalid sequence number!")
                self.send_pkts[ii] = gnuradio.GnuradioPacket() / dot15d4.Dot15d4FCS(
                    bytes(packet_bytes[:-2])
                    + self.send_pkts[ii].compute_fcs(
                        bytes(packet_bytes[:-2])
                    )  # re-compute the FCS after modifying the seq number
                )
        elif modify_type == 1 or modify_type == 3:
            ii = 0
            while ii < len(self.send_pkts):
                packets_bytes = [
                    bytearray(bytes(pkt))
                    for pkt in self.send_pkts[ii: ii + self.single_replay_length]
                ]
                while True:
                    try:
                        if modify_type == 1:
                            for jj in range(len(packets_bytes)):
                                seq_new = packets_bytes[jj][2] + seq_add
                                if seq_new > 255:
                                    seq_new %= 255
                                packets_bytes[jj][2] = seq_new
                            seq_add += 1
                        else:
                            iot_click.print("\n")
                            for jj in range(
                                len(self.send_pkts[ii: ii +
                                                   self.single_replay_length])
                            ):
                                iot_click.print(
                                    "{}: {}".format(
                                        jj, self.send_pkts[jj].summary())
                                )
                            iot_click.print(
                                "Current group sequence numbers: {}".format(
                                    list([pkt_bytes[2]
                                          for pkt_bytes in packets_bytes])
                                )
                            )
                            new_seq_number = iot_click.prompt(
                                "New sequence number", type=click.IntRange(0, 255)
                            )
                            for jj in range(len(packets_bytes)):
                                packets_bytes[jj][2] = new_seq_number
                        break
                    except ValueError:
                        print("Invalid sequence number!")
                self.send_pkts[ii: ii + self.single_replay_length] = [
                    gnuradio.GnuradioPacket()
                    / dot15d4.Dot15d4FCS(
                        bytes(pkt_bytes[:-2])
                        + dot15d4.Dot15d4FCS().compute_fcs(bytes(pkt_bytes[:-2]))
                    )
                    for pkt_bytes in packets_bytes
                ]
                ii += self.single_replay_length

    def prompt_wait_times(self):
        """Prompts the user for wait times after each packet transmission
        """
        if self.wait_times is None and iot_click.confirm(
            "Wait after each packet transmission?"
        ):
            while self.wait_times is None or self.wait_times < 0:
                self.wait_times = iot_click.prompt(
                    "How long do you want to wait after each packet transmission (s)",
                    type=click.FLOAT,
                )

    def evaluate_input_bytes(self, in_bytes):
        """Evaluates a string form of raw bytes from a prompt, then converts
        and returns this string into actual bytes.

        Arguments:
            in_bytes {str} -- Bytes in one of the following forms:
                                Byte String: \\x00\\xff\\x0a\\x04"
                                Space-Delimited Hex: 00 FF 0A 04"
                                Comma-Delimited Hex: 00,FF,0A,04"

        Returns:
            [type] -- [description]
        """
        if "\\" in in_bytes:
            try:
                assert len(in_bytes) > 1
                if "b'" != in_bytes[:2]:
                    in_bytes = "b'" + in_bytes
                if in_bytes[-1] != "'":
                    in_bytes += "'"
                return ast.literal_eval(in_bytes)
            except (ValueError, SyntaxError, AssertionError):
                print("Invalid byte sequence!")
                return None
        else:  # technically you can mix comma-delimited and space delimited, but who would want to do that
            try:
                in_bytes = bytes.fromhex(in_bytes.replace(",", ""))
                return in_bytes
            except (ValueError, SyntaxError):
                print("Invalid byte sequence!")
                return None

    def choose_indexes(self, packets, click_override=True):
        """Given a list, choose specific indexes and return a new list
        formed from these chosen indexes

        Arguments:
            packets {list} -- List of packets to dissect

        Keyword Arguments:
            click_override {bool} -- Whether or not to override click prompts and prints
                with iot_click (default: {True})

        Returns:
            {list} -- The list of packets after specific indexes are chosen
        """
        while True:
            iot_click.print(
                "\nEnter the indexes (in send order) of the packet(s) to transmit. Possible formats:",
                override=click_override,
            )
            iot_click.print("  Single index: 1", override=click_override)
            iot_click.print("  Several indexes: 1,3,2",
                            override=click_override)
            iot_click.print("  All indexes: all", override=click_override)
            chosen_indexes = iot_click.prompt(
                "Enter your desired packet indexes", override=click_override
            )
            chosen_packets = []
            if chosen_indexes == "all":
                chosen_packets = packets
                break
            else:
                try:
                    chosen_indexes = ast.literal_eval(chosen_indexes)
                    assert (
                        isinstance(chosen_indexes, int)
                        or isinstance(chosen_indexes, tuple)
                        or isinstance(chosen_indexes, list)
                    )
                except (ValueError, SyntaxError, AssertionError):
                    print("Invalid choice(s)!")
                if isinstance(chosen_indexes, int):
                    try:
                        chosen_packets = [packets[chosen_indexes]]
                        break
                    except IndexError:
                        print("Index out of range. Pick again")
                else:
                    send_packets = []
                    for index in chosen_indexes:
                        try:
                            send_packets.append(packets[index])
                        except IndexError:
                            print("Index out of range. Pick again")
                            send_packets = []
                    chosen_packets = send_packets
                    break
        if len(chosen_packets) > 1 and iot_click.confirm(
            "Use time deltas of timestamps to wait between packet transmissions?",
            override=click_override,
        ):
            self.wait_times = [pkt.time for pkt in chosen_packets]
            for ii in range(len(chosen_packets) - 1):
                self.wait_times[ii] = self.wait_times[ii + 1] - \
                    self.wait_times[ii]
                if self.wait_times[ii] < 0:
                    print(
                        "Error! Some timestamps were ahead of others. Resetting wait times between transmissions"
                    )
                    self.wait_times = None
                    break
            if self.wait_times is not None:
                # don't wait at all after the last packet
                self.wait_times[-1] = 0
        return chosen_packets

    def view(self):
        """Interactive view of packets received during the transmit
        """
        pkt_table = PrettyTable()
        pkt_table.field_names = ['#', 'Timestamp', 'Packet Summary']
        pkt_table.align = 'l'
        for ii in range(len(self.packets_rx)):
            pkt_table.add_row(
                [
                    ii,
                    self.packets_rx[ii].time,
                    '{:.100s}'.format(self.packets_rx[ii].summary()),
                ]
            )
        while 1:
            print('\n\n')
            print(pkt_table)
            try:
                index = click.prompt(
                    "\nEnter the index of a packet to see more details, or leave blank to exit",
                    type=click.IntRange(0, len(self.packets_rx) - 1),
                    default=-1,
                    show_default=False,
                )
            except click.Abort:
                break
            if index == -1:
                break
            else:
                print()
                self.packets_rx[index].show()
                click.prompt(
                    "\nPress enter to continue", default="", show_default=False
                )

    def handle_packet(self, pkt, tx=False):
        """Handles the packets while the sniff is running

        Arguments:
            pkt {scapy.Packet} -- The packet sent/received

        Keyword Arguments:
            tx {bool} -- True if this is a transmitted packet,
                            False if a received packet (default: {False})
        """
        if tx:
            self.packets_tx.append(pkt)
            print(
                "Sent Packet #{number}: {summary}".format(
                    number=len(self.packets_tx),
                    summary=pkt.payload.summary(),
                )
            )
            pkt.sent_time = time.time()
            print(f"Pkt Sent Time: {pkt.sent_time}")
        else:
            pkt = rftap.RFtap(pkt)
            print(
                "Received packet at {timestamp}: {summary}".format(
                    timestamp=pkt.time,
                    summary=pkt.payload.summary(),
                )
            )
            self.packets_rx.append(pkt)
        scapy.wrpcap(self.filename, pkt, append=True)

    def populate_settings(self):
        """Prompts the user or uses iot_click's automatic member
        to find all of the settings needed for the transmission
        """
        if not self.send_pkts:
            iot_click.print("\nChoose a Transmission Type:")
            iot_click.print('  0: "Hello World" 802.15.4 Data')
            iot_click.print("  1: Raw packet bytes")
            iot_click.print(
                "  2: Pcap packets (can choose which packets to transmit)")
            iot_click.print(
                "  3: Listen and replay (can choose which packets to replay)"
            )
            send_type = iot_click.prompt(
                "Your choice", type=click.IntRange(0, 3))
            if send_type == 0:
                self.send_pkts = [
                    gnuradio.GnuradioPacket()
                    / dot15d4.Dot15d4FCS()
                    / dot15d4.Dot15d4Data()
                    / "Hello world!"
                ]
            elif send_type == 1:
                self.prompt_raw_bytes()
            elif send_type == 2:
                self.prompt_pcap()
            elif send_type == 3:
                self.prompt_replay()
        else:
            send_type = -1  # set to -1 if packets were already given
        if not self.send_pkts:
            print("\nNo packets received")
            return
        while self.send_num is None or self.send_num < 1:
            self.send_num = iot_click.prompt(
                "Enter the number of transmission replays for the chosen packets",
                type=click.INT,
                default=1,
            )
        self.single_replay_length = len(self.send_pkts)
        self.send_pkts *= self.send_num
        if isinstance(self.wait_times, list):
            self.wait_times *= self.send_num
        self.prompt_modify_sequence()
        self.prompt_wait_times()

    def open_wireshark(self):
        """Opens up wireshark with the data
        """
        subprocess.run(["wireshark", self.filename])

    def run(self):
        """Runs the transmission
        """
        self.populate_settings()
        if self.preamble_min:
            params = {
                'preamble_min': self.preamble_min,
                'preamble_max': self.preamble_max,
            }
        else:
            params = {}
        self.start_time = time.time()
        try:
            self.radio.switch_mode('Zigbee', ['rf', 'tx'])
            for ch in self.channels:
                self.radio.set_channel(ch)
                ch_start_time = time.time()
                print("\nSending on channel {}".format(ch))
                self.radio.srradio(
                    self.send_pkts,
                    channels=self.channels,
                    prn=self.handle_packet,
                    wait_times=self.wait_times,
                    env=self.env,
                    params=params,
                )
                if len(self.channels) > 1:
                    print(
                        "Total Time for Channel {}: {}".format(
                            ch,
                            datetime.timedelta(seconds=round(
                                (time.time() - ch_start_time), 4)
                            ),
                        )
                    )
        except ConnectionRefusedError:
            # don't raise since any keyboard interrupt with a XMLRPC dependent flow graph will throw this on a keyboard interrupt
            print('Socket ConnectionRefusedError')
            pass
        except KeyboardInterrupt:
            pass
        self.conclude()

    def conclude(self):
        """Concludes a transmission by printing out summaries + test results

        Returns:
            {list} -- the packets received during the transmission
        """
        self.radio.close_socket()
        if self.radio.full_duplex:  # not full duplex, so won't receive anything...only tx
            if self.packets_rx:
                if self.display:
                    self.view()
            else:
                print("\nNo packets received")
        if self.wireshark:
            self.open_wireshark()
        log_table = PrettyTable()
        log_table.field_names = ['Log Type', 'Value']
        log_table.add_row(['Gnuradio Stdout:', '/tmp/gnuradio.log'])
        log_table.add_row(['Gnuradio Stderr:', '/tmp/gnuradio-err.log'])
        log_table.add_row(['File Dump:', self.filename])
        log_table.add_row(['Total Time:', datetime.timedelta(
            seconds=round((time.time() - self.start_time), 4))]
        )
        print()
        print(log_table)
        return self.packets_rx
