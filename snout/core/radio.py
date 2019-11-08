import datetime
import json
import os
import subprocess
import sys
import time
from pydoc import locate

import click

import scapy.modules.gnuradio as gnu_scapy
from prettytable import PrettyTable
from scapy.all import conf, load_module, subprocess
from scapy.modules.gnuradio import (GnuradioSocket, gnuradio_set_vars,
                                    initial_setup, kill_process, sendrecv,
                                    strip_gnuradio_layer,
                                    switch_radio_protocol)
from snout.core import EventMgmtCapability, LoggingCapability, RequiredCapability
from snout.core.config import Config as cfg
from snout.core.protocols import *
from snout.core.ui import ScanUIHandler, UIType


class AbstractSelector(object):
    """ This class handles selecting a handler class based on a protocol.

    Typically, handler classes have a lot of commonality and are called in a similar way,
    this class facilitates the process and reduces code duplication.
    """
    handlers = {}

    @classmethod
    def get_instance(cls, protocol, **kwargs):
        if protocol in cls.handlers:
            handler_class = locate(cls.handlers[protocol])
            return handler_class(**kwargs) # Calls the handler class with all passed arguments
        raise NotImplementedError(f"{cls.__name__} does not know a Scanner class for the {protocol} protocol.")

    @classmethod
    def select(cls, protocol, ctx_obj):
        raise NotImplementedError("Please implement a specialized selector class.")

class ScanSelector(AbstractSelector):
    """ This class handles selecting the right scan class based on a protocol.
    """
    handlers = {
        BTLE:       'snout.util.btle.BtleScan',
        WIFI:       'snout.util.wifi.WifiScan',
        ZIGBEE:     'snout.util.zigbee.ZigbeeScan',
        ZWAVE:      'snout.util.zwave.ZWaveScan',
    }

    @classmethod
    def select(cls, protocol, ctx_obj):
        return cls.get_instance(protocol, 
                active      = ctx_obj['scan']['active'],
                channels    = ctx_obj['scan']['channels'],
                env         = ctx_obj['app'].env,
                display     = ctx_obj['display'],
                filename    = ctx_obj['filename'],
                radio       = ctx_obj['app'].radio,
                packet_threshold = ctx_obj['scan']['num'],
                timeout     = ctx_obj['scan']['timeout'],
                wireshark   = ctx_obj['wireshark'],
            )

class TransmitSelector(AbstractSelector):
    """ This class handles selecting the right transmit class based on a protocol.
    """
    handlers = {
        ZIGBEE:     'snout.util.zigbee.ZigbeeTransmission',
    }

    @classmethod
    def select(cls, protocol, ctx_obj):
        return cls.get_instance(protocol, 
                channels    = ctx_obj['transmit']['channels'],
                env         = ctx_obj['app'].env,
                display     = ctx_obj['display'],
                filename    = ctx_obj['filename'],
                radio       = ctx_obj['app'].radio,
                wireshark   = ctx_obj['wireshark'],
            )


class Radio(LoggingCapability, EventMgmtCapability, RequiredCapability):

    # TODO Implement the Pluto SDR in detect_hardware and modulation flowgraphs

    FULL_DUPLEX = ['usrp', 'pluto']

    def __init__(self, hardware=None, detect=True, env=None, parent=None):
        super().__init__()
        self._required_attrs = ['hardware', 'protocols']

        load_module('gnuradio')
        # usrp, hackrf, etc.
        self.env = env
        self.parent = parent
        # full_duplex detected in self.detect_hardware if no hardware is given
        self.full_duplex = hardware in self.FULL_DUPLEX if hardware else None
        self.hardware = hardware.lower() if hardware else None
        if detect:
            self.detect_hardware()
        self.protocols = {}
        self.update_protocols()
        self._socket = None
        self.current_channel = None

    def update_protocols(self):
        """Update the protocols available to this protocol based on
        the conf.gr_modulations dict from scapy
        """
        try:
            for protocol, hardwares in conf.gr_modulations.items():
                if self.hardware in hardwares.keys():
                    self.protocols[protocol] = conf.gr_modulations[protocol][self.hardware]
        except AttributeError:  # conf.gr_modulations hasn't been loaded up yet
            initial_setup()
            self.update_protocols()

    def protocol_modes(self, protocol):
        """Find the modes available for this hardware and a specific protocol

        Arguments:
            protocol {str} -- String representation of the protocol

        Returns:
            {list} -- The available modes for the protocol and radio hardware
        """
        protocol = protocol.lower()
        self.update_protocols()
        return list(self.protocols[protocol].keys())

    def detect_hardware(self):
        """Detects the hardware available by running the commands
        found in the hardware_checks list and detecting if a 0 status
        code is returned (availble) or a 1 status code is returned (not available).

        Currently, if a specific hardware is not set in self.hardware, then the
        hardware that is higher up in the hardware_checks list will be given priority.
        If a hardware is added to the list, it should be added to hardware_checks in
        as a tuple in the form of: (hardware_str, find_cmd). Ex: ('hackrf', 'hackrf_info')

        Returns:
            str -- The hardware that was found. None if no hardware was found
        """
        hardware_checks = [
            ('usrp', 'uhd_find_devices'),
            ('hackrf', 'hackrf_info')
        ]
        if self.hardware:  # if using a specific hardware, only try to detect the given hardware type
            supported = False
            for hardware_info in hardware_checks:
                if hardware_info[0] == self.hardware:
                    hardware_checks = [hardware_info]
                    supported = True
                    break
            if not supported:
                print("Could not find supported hardware\n")
                self.hardware = None
                return self.hardware
        print("\nTrying to find supported hardware: {}".format(
            ', '.join(hardware_info[0] for hardware_info in hardware_checks))
        )
        for hardware_info in hardware_checks:
            try:  # try to find a usrp first, since full duplex is optimal for testing
                find_process = subprocess.check_call(
                    hardware_info[1], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, env=self.env)
                if find_process == 0:
                    print(f"Using hardware: {hardware_info[0]}")
                    self.hardware = hardware_info[0]
                    self.full_duplex = self.hardware in self.FULL_DUPLEX
                    return self.hardware
            except (FileNotFoundError, subprocess.CalledProcessError):
                # if they don't have this hardware's drivers (FileNotFoundError) or one is not plugged in (returns exit code 1), just move on and try for the next hardware
                pass
        print("Could not find supported hardware")
        self.hardware = None
        return self.hardware

    @property
    def socket(self):
        if self._socket is None:
            # set to a fresh GnuradioSocket if one does not exist
            self._socket = GnuradioSocket()
        return self._socket

    @socket.setter
    def socket(self, value):
        self._socket = value

    def close_socket(self):
        """Close the socket if it exists

        Returns:
            {bool} -- True if closed, False if nothing done (socket
                        is already closed or doesn't exist)
        """
        if self._socket:
            self._socket.close()
            return True
        return False

    def kill_process(self):
        if conf.gr_process:
            kill_process()  # see the scapy gnuradio module

    def sniffradio(
        self,
        opened_socket=None,
        params={},
        prn=None,
        *args,
        **kwargs
    ):
        """Starts sniffing on the SDR, assuming that the correct protocol
        and mode has already been switched to.

        Keyword Arguments:
            opened_socket {socket} -- Socket to use. If None then one is created (default: {None})
            params {dict} -- Any params to send to the XMLRPC Server. Keys are the
                                variable names, values are their values (default: {{}})
            prn {func} -- Function to call when a packet is received (default: {None})

        Returns:
            {list} -- Packets received during the sniff
        """
        if opened_socket:
            self.socket = opened_socket
        gnuradio_set_vars(**params)
        rv = sendrecv.sniff(
            opened_socket=self.socket,
            prn=(lambda x: prn(strip_gnuradio_layer(x))) if prn else None,
            *args,
            **kwargs
        )
        rx_packets = rv
        return rx_packets

    def switch_mode(self, protocol, modes):
        mode = switch_radio_protocol(
            protocol.lower(),
            hardware=self.hardware,
            env=self.env,
            modes=modes
        )
        return True if mode else False

    def set_channel(self, channel):
        """Sets the channel variable over the XMLRPC Server.

        This method assumes that the GNURadio flowgraph has a
        variable or parameter called "channel" that helps determine
        the frequency that the radio is set to 

        Arguments:
            channel [int, float] -- Value to set the channel variable to
        """
        self.current_channel = channel
        gnuradio_set_vars(channel=channel)

    def srradio(
        self,
        pkts,
        wait_times=0.20,
        params={},
        prn=None,
        *args,
        **kwargs
    ):
        """Send and Receive using a Gnuradio socket

        If the radio is not full duplex, then this method will only send packets.

        Arguments:
            pkts {list} -- List of packets to send

        Keyword Arguments:
            wait_times [list, int, float] -- list of times to wait after each packet is sent or a single
                                                numeral to wait the same amount of time after each (default: {0.20})
            params {dict} -- [description] (default: {{}})
            params {dict} -- Any params to send to the XMLRPC Server. Keys are the
                                variable names, values are their values (default: {{}})
            prn {func} -- Function to call when a packet is received or sent (default: {None})

        Returns:
            list -- packets received during the transmission (does not include sent packets)
        """
        pkt_strings = [str(pkt) for pkt in strip_gnuradio_layer(pkts)]
        rx_packets = []
        gnuradio_set_vars(**params)
        if not wait_times:
            wait_times = [0.01]*len(pkts)
        elif not isinstance(wait_times, list):  # either list, numeral, or None
            wait_times = [wait_times] * len(pkts)
        for ii in range(len(pkts)):
            self.socket.send(pkts[ii])
            if prn:
                prn(pkts[ii], tx=True)
            if wait_times[ii] and wait_times[ii] > 0.05:  # > 0.05 to lessen prints
                print(f"Waiting {wait_times[ii]} seconds...")
            if self.full_duplex:
                rv = sendrecv.sniff(
                    opened_socket=self.socket,
                    timeout=wait_times[ii],
                )
                for r_pkt in rv:
                    r_pkt = strip_gnuradio_layer(r_pkt)
                    if (r_pkt is not None and str(r_pkt) != pkt_strings[ii]):
                        if prn:
                            prn(r_pkt)
                        rx_packets.append(r_pkt)
            else:
                time.sleep(wait_times[ii])
        return rx_packets





class SDRController(LoggingCapability, EventMgmtCapability, RequiredCapability):

    def __init__(self, **kwargs):
        super().__init__()
        self._required_attrs = ['channels']
        self.missing_settings = []
        self.active = kwargs.pop('active', None)
        channels = kwargs.pop('channels', None)
        if isinstance(channels, list):
            self.channels = channels
        elif isinstance(channels, int):
            self.channels = [channels]
        else:
            self.channels = []
        self.env = kwargs.pop('env', None)
        self.protocol = kwargs.pop('protocol', None)
        self.packet_threshold = kwargs.pop('packet_threshold', None)
        self.radio = kwargs.pop('radio', None)
        self.timeout = kwargs.pop('timeout', None)
        self.wireshark = kwargs.pop('wireshark', None)
        self.packets = []
        self.start_time = None
        self._file_extension = kwargs.pop('file_extension', '.pcap')
        self.filename = kwargs.pop('filename', None)

    def run(self):
        raise NotImplementedError

    @property
    def filename(self):
        return self._filename
    
    @filename.setter
    def filename(self, filename):
        """Creates a path to the correct filename based off of the given
        filename and file_extension. If filename is not None then it will
        be checked to make sure it is valid (create any needed directories)
        and then returned. If filename is None, then a timestamped file with 
        the protocol name will be created with a file extension that is by 
        default ".pcap" (set in self.__init__)

        Arguments:
            filename {str} -- The filename (including the extension) 
            file_extension {str} -- The file extension type. ex: ".pcap"

        Returns:
            {str} -- Path to the file
        """
        label = '{}_{}{}'.format(
            self.protocol,
            datetime.datetime.now().strftime("%Y-%m-%d.%H:%M:%S"),
            self._file_extension
        )
        if filename:
            if os.path.isdir(filename):
                if not os.path.exists(filename):
                    os.makedirs(filename, exist_ok=True)
                self._filename = os.path.join(filename, label)
            else:
                if not os.path.exists(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename), exist_ok=True)
                self._filename = filename
        if not os.path.exists(cfg.OUTPUTS_DIR):
            os.makedirs(cfg.OUTPUTS_DIR, exist_ok=True)
        self._filename = os.path.join(cfg.OUTPUTS_DIR, label)


class Scan(SDRController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.display = kwargs.pop('display', None)

    def handle_packet(self):
        """Handles the packets while the sniff is running
        """
        raise NotImplementedError

    def run(self):
        """Runs the scan

                The scan stops when each channel has reached a timeout and/or has collected
                a certain number of packets. May implement a total timeout or total number of
                packets to collect across all channels later.

                Returns:
                        self.packets at the end of the scan
        """
        self.start_time = time.time()
        params = {}
        try:
            if not self.radio.switch_mode(self.protocol, 'rx'):
                print(f'Could not find a valid rx file for {self.protocol}')
                sys.exit(1)
            for ch in self.channels:
                self.radio.set_channel(ch)
                ch_start_time = time.time()
                print(f"\nSniffing on channel {ch}")
                self.radio.sniffradio(
                    prn=self.handle_packet,
                    stop_filter=self.check_stop,
                    timeout=self.timeout,
                    count=self.packet_threshold,
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
        except (KeyboardInterrupt, click.Abort):
            pass  # still form the CLI command
        self.conclude()

    def conclude(self):
        """Concludes a scan by printing out summaries + test results

        Returns:
            {list} -- the packets received from the scan
        """
        self.radio.close_socket()
        if self.packets:
            if self.display:
                self.view()
            if self.wireshark:
                self.open_wireshark()
        else:
            print("\nNo packets received")
        log_table = PrettyTable()
        log_table.field_names = ['Log Type', 'Value']
        log_table.add_row(
            ['Gnuradio Stdout:', gnu_scapy.output()['stdout'].name]
        )
        log_table.add_row(
            ['Gnuradio Stderr:', gnu_scapy.output()['stderr'].name]
        )
        log_table.add_row(['File Dump:', self.filename])
        log_table.add_row(
            [
                'Total Time:', datetime.timedelta(
                    seconds=round((time.time() - self.start_time), 4))
            ]
        )
        print("")
        print(log_table)
        return self.packets

    def check_stop(self, num_packets):
        """Checks if the scan should stop, and stops the controlled process if it should.

        Returns:
                True if the scan should be stopped
                False if the scan should continue
        """
        raise NotImplementedError

    def open_wireshark(self):
        """Opens up wireshark with the data
        """
        subprocess.Popen(["wireshark", self.filename])

    def view(self):
        """Interactive view of packets found from the scan
        """
        pkt_table = PrettyTable()
        pkt_table.field_names = ['#', 'Timetsamp', 'Packet Summary']
        pkt_table.align = 'l'
        for ii in range(len(self.packets)):
            pkt_table.add_row(
                [
                    ii,
                    self.packets[ii].time,
                    '{:.100s}'.format(self.packets[ii].summary()),
                ]
            )
        while 1:
            print('\n\n')
            print(pkt_table)
            try:
                index = click.prompt(
                    "\nEnter the index of a packet to see more details, or leave blank to exit",
                    type=click.IntRange(0, len(self.packets) - 1),
                    default=-1,
                    show_default=False,
                )
            except click.Abort:
                break
            if index == -1:
                break
            else:
                print()
                self.packets[index].show()
                click.prompt(
                    "\nPress enter to continue", default="", show_default=False
                )

class Transmission(SDRController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.display = kwargs.pop('display', None)
        self.start_time = 0
        self.packets_rx = []
        self.packets_tx = []
        self.send_num = kwargs.pop('send_num', None)
        self.send_pkts = kwargs.pop('send_pkts', [])
        self.wait_times = kwargs.pop('wait_times', None)
