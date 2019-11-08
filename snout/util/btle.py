import codecs
import datetime
import json
import logging
import os
import time
from shutil import get_terminal_size

import click
import timeago

import snout.core.protocols as proto
from prettytable import PrettyTable
from snout.core.device import Device
from snout.core.message import BtleMessage
from snout.core.radio import Scan
from snout.core import Event
from snout.core.ui import ScanUIHandler, UIType
from snout.core.pcontroller import PController


class BtleScan(Scan):
    """Helps to perform a bluetooth scan.
    """

    def __init__(
        self,
        active=None,
        channels=None,
        display=None,
        env=None,
        filename=None,
        packet_threshold=None,
        radio=None,
        timeout=None,
        wireshark=None,
        ui_type=UIType.summary
    ):
        super().__init__(
            active=active,
            channels=channels,
            display=display,
            env=env,
            filename=filename,
            file_extension='.b',
            packet_threshold=packet_threshold,
            protocol=proto.BTLE,
            timeout=timeout,
            wireshark=wireshark,
        )

        self.radio = radio
        self.scan_process = PController("btle_rx", env=self.env)
        self.save_file = open(self.filename, "wb")
        self.devices = {}

    def run(self):
        """Runs the scan. Doesn't use scapy / sockets,
        so the run method in util/scan.py is not used for BTLE
        """
        self.start_time = time.time()
        for ch in self.channels:
            self.scan_process.args = {
                "-c": str(ch),
                "-g": "6",
                "-a": "8e89bed6",
                "-k": "555555",
            }
            self.scan_process.run()
            print("\nCapturing on channel {}\n".format(str(ch)))
            try:
                while self.scan_process.is_running():
                    self.handle_packet(
                        line=self.scan_process.readline(decode=False))
                    if self.check_stop():
                        break
            except KeyboardInterrupt:
                break  # End the test if keyboard interrupt
        self.conclude()

    def conclude(self):
        """See util/scan.py
        """
        if self.wireshark:
            print("\nNo wireshark feature yet")
        if self.display:
            self.view()
        log_table = PrettyTable()
        log_table.field_names = ['Log Type', 'Value']
        log_table.add_row(['File Dump:', self.filename])
        log_table.add_row(['Total Time:', datetime.timedelta(
            seconds=round((time.time() - self.start_time), 4))])
        print()
        print(log_table)
        self.save_file.close()
        return self.packets

    def handle_packet(self, line):
        """See util/scan.py
        """
        message = BtleMessage.fromraw(line)
        # Only continue if message is valid.
        if not message:
            return False
        if self.save_file:
            self.save_file.write(line)
        self.packets.append(message)
        self.emitEvent(Event(self.eventName(proto.BTLE,'packet-received'), message=message))
        return True

    def check_stop(self):
        """See util/scan.py
        """
        if self.packet_threshold:
            if len(self.packets) >= self.packet_threshold:
                self.scan_process.stop()
                return True
        if self.timeout:
            if time.time() - self.scan_process.start_time >= self.timeout:
                self.scan_process.stop()
                return True
        return False

## TODO ##
# Get rid of parse_devices and view...keeping for now due to CLI compatibility

    def parse_devices(self):
        """Parses the devices from a scan

            Takes the packets list from a completed scan, and creates a dictionary of
            dictionaries, with the mac address as the key and a dictionary of info
            as the content
        """
        for packet in self.packets:
            mac = packet.get("mac", None)
            if mac:
                if mac in self.devices:
                    self.devices[mac]["number"] += 1
                    self.devices[mac]['packets'].append(packet)
                else:
                    self.devices[mac] = {}
                    self.devices[mac]["number"] = 1
                    self.devices[mac]['packets'] = [packet]
                    if "manufacturer-specific" in packet:
                        self.devices[mac]["vendor"] = packet["company_name"]

    def view(self):
        self.parse_devices()
        pkt_table = PrettyTable()
        pkt_table.field_names = ['#', 'MAC', 'Appearances', 'Vendor']
        pkt_table.align = 'l'
        ii = 0
        device_list = [
            {
                'mac': mac,
                'data': data
            }
            for mac, data in self.devices.items()
        ]
        appearances_list = [device_list[ii]['data']['number']
                            for ii in range(len(device_list))]
        device_list = [
            device for _, device in sorted(
                zip(appearances_list, device_list),
                key=lambda pair: pair[0],
                reverse=True)
        ]
        for ii in range(len(device_list)):
            pkt_table.add_row(
                [
                    ii + 1,
                    device_list[ii]['mac'],
                    device_list[ii]['data']['number'],
                    device_list[ii]['data']['vendor'] if 'vendor' in device_list[ii]['data'] else None,
                ]
            )
        while 1:
            print('\n\n')
            print(pkt_table)
            try:
                index = click.prompt(
                    "\nEnter the index of a device to see more details, or leave blank to exit",
                    type=click.IntRange(1, len(self.devices)),
                    default=0,
                    show_default=False,
                ) - 1
            except click.Abort:
                break
            if index == -1:
                break
            else:
                print()
                print()
                for packet in device_list[index]['data']['packets']:
                    print(json.dumps(packet, indent=4,
                                     default=str, sort_keys=True))
                click.prompt(
                    "\nPress enter to continue", default="", show_default=False
                )


class BtleScanUIHandlerSummary(ScanUIHandler):
    def __init__(self, type):
        super().__init__(type)
        self.update_interval = 1

    def print_summary(self):
        """See util/scan.py
        """
        recent_devices = sorted(Device.instances.get(
            proto.BTLE, []), key=lambda d: d.last_seen, reverse=True)
        recent_devices = [
            d for d in recent_devices if len(d.messages_sent) > 0]
        output = PrettyTable()
        output.field_names = ['MAC', 'Last Seen',
                                '#', 'Up', 'Vendor', 'Model', 'OS', 'Info']
        for i, device in enumerate(recent_devices):
            if i > 50:
                break
            output.add_row([device.id, device.last_seen_nice, device.occurrences,
                            device.uptime_nice, device.vendor, device.model, device.os, device.activity])
        _, lines = get_terminal_size()
        # limit max table length
        tab_output = output.get_string() \
            if len(output._rows) < lines-6 \
            else output[0:lines-6].get_string() \
                + '\n[%d most recent shown, %d omitted]' % (lines-6, len(output._rows)-(lines-6))
        # prettify short table printing by padding with newlines
        print( '\n'*max( 0, lines-len(tab_output.splitlines()) ) )
        # print table
        print(tab_output)
        #print(lines, len(output._rows), (len(output._rows)-(lines-6)) )
        self.updated_ui()

    def __call__(self, *args, **kwargs):
        m = kwargs.get('message', None)
        if m:
            self.packets.append(m)
        if self.check_update_ui():
            self.print_summary()

