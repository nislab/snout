import json
import time

from scapy.packet import Packet
import scapy.layers as layers
from snout.core.protocols import *
from snout.core.device import Device
from snout.core.protocols.btle.advertising import BtlePDUPayload


class Message(object):
    def __init__(self, protocol, sender=None, receiver=None, **kwargs):
        self.protocol = protocol
        self.timestamp = kwargs.pop('timestamp', time.time())
        self.number = int(kwargs.pop('number', -1))
        self.vuln = kwargs.pop('vuln', {})
        self.sender = sender
        self.receiver = receiver
        self.payload = kwargs.pop('payload', None)
        self.raw = kwargs.pop('raw_message', None)
        self.seq_number = kwargs.pop('seq_number', None)
        self.meta = kwargs

    @classmethod
    def find_field(cls, message, field):
        """Tries to find a field and return its value in the message. 
        If it does not exist, then return None. This is useful for
        scapy messages, which have many different fields

        Arguments:
            message {scapy.Packet} -- Message to search in...typically a scapy Packet
            field {str} -- the field name to search for
        """
        getattr(message, field) if hasattr(message, field) else None

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = float(value)

    @property
    def sender(self):
        return self._sender

    @sender.setter
    def sender(self, value):
        """Sets the sender, but also appends the message to the sender device from
        the Device class found in core/device.py

        If the sender already has an associated device, then this device is found
        using Device.get_unique and the message is appended to this device's 
        messages_sent member. Otherwise, Device.get_unique will create a new device
        with this sender.

        Arguments:
            value {str} -- The sender address (typically a MAC address)
        """
        device = Device.get_unique(self.protocol, value)
        device.messages_sent.append(self)
        self._sender = device

    @property
    def receiver(self):
        return self._receiver

    @receiver.setter
    def receiver(self, value):
        """Similar to self.sender, this method will find an existing receiver device
        or create a new one depending on the address.

        If vulnerabilities were parsed within the message, then if the vulnerability
        was not already found for the device, it will be set to the value of the
        found vulnerability (typically k is the vulnerability name, and v is True
        if it is vulnerable, and False otherwise).

        Arguments:
            value {str} -- The receiver address (typically a MAC address)
        """
        device = Device.get_unique(self.protocol, value)
        device.messages_received.append(self)
        for k, v in self.vuln:
            if v and k not in device.vuln or not device.vuln[k]:
                device.vuln[k] = v
        self._receiver = device

    @property
    def payload(self):
        """Gets the payload. If this is a scapy packet, then the payload is found
        by looping through the layers until the highest layer is reached (the layer
        that has no payload)

        Returns:
            [str, bytes] -- The packet payload
        """
        if not self._payload and isinstance(self.raw, Packet):
            layer = self.raw
            layer_count = 1
            while layer.payload is not None:
                layer = self.raw.getlayer(layer_count)
                layer_count += 1
            self._payload = layer  # should be at the payload layer since layer.payload is None
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value

    @property
    def raw(self):
        return self._raw

    @raw.setter
    def raw(self, value):
        self._raw = value

    @property
    def seq_number(self):
        return self._seq_num

    @seq_number.setter
    def seq_number(self, value):
        self._seq_num = value

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, value):
        self._number = value

    @property
    def meta(self):
        return self._meta

    @meta.setter
    def meta(self, value):
        self._meta = value if isinstance(value, dict) else {}

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, value):
        if value not in PROTO:
            raise ValueError(
                f"{value} is not a valid message protocol (Must be out of {PROTO}).")
        self._protocol = value

    @property
    def vuln(self):
        return self._vuln

    @vuln.setter
    def vuln(self, value):
        self._vuln = value

    def dict(self):
        """Creates a dictionary representation of the message with the
        members that that are useful to display

        Returns:
            {dict} -- Dictionary representation of the message
        """
        printables = [
            'protocol', 'timestamp', 'sender', 'receiver',
            'seq_number', 'number', 'meta', 'raw', 'payload'
        ]
        display_dict = {}
        for printable in printables:
            printable_attr = getattr(self, printable)
            if hasattr(printable_attr, 'dict'):
                display_dict[printable.title()] = printable_attr.dict()
            else:
                display_dict[printable.title()] = printable_attr
        return display_dict

    def json(self, indent=4):
        """Creates a json formatted string of the message from what is returned
        by self.dict

        Keyword Arguments:
            indent {int} -- The spaces to indent by (default: {4})

        Returns:
            {str} -- json formatted string representation of the message
        """
        return json.dumps(self.dict(), indent=4, default=str)


class BtleMessage(Message):
    """BTLE Specific Message Class.
    """

    def __init__(self, sender=None, channel=None, pdu_type=None, pdu_payload=BtlePDUPayload(), access_address='8e89bed6', **kwargs):
        super().__init__(BTLE, sender, **kwargs)
        self.pdu_type = pdu_type
        self.pdu_payload = pdu_payload
        self.access_address = access_address

    @classmethod
    def fromraw(cls, raw_message):
        """Create a BTLE specific message from the raw bytes

        In this case, the raw bytes are the full line output from 
        Xianjun Jiao's BTLE software btle_rx mode is parsed.

        Example raw_message:

        1567108496.651985 Pkt8 Ch37 AA:8e89bed6 ADV_PDU_t0:ADV_IND T1 R0 PloadL20 AdvA:6385725ebfcd Data:0201060aff4c001005011c569415 CRC1
        {epoch time} {Pkt#} {Ch#} {Access Address} {PDU Type} {Data / Payload} {CRC}

        Arguments:
            raw_message {bytes} -- Full line output from btle_rx

        Returns:
            {Message} -- the formed message
        """
        if not raw_message:
            return False
        split_message = raw_message.decode().split(" ")
        if split_message[-1] != 'CRC0\n' or len(split_message) != 11:
            return False
        m = BtleMessage(
            sender=split_message[8][5:],
            channel=split_message[2][2:],
            pdu_type=split_message[4][11:],
            pdu_payload=BtlePDUPayload.fromstring(split_message[9][5:]),
            raw_message=raw_message,
            timestamp=split_message[0],
            number=split_message[1][3:]
        )
        return m

    @property
    def pdu_payload(self):
        return self._payload

    @pdu_payload.setter
    def pdu_payload(self, value):
        if not isinstance(value, BtlePDUPayload):
            raise TypeError("PDU Payload must be a :class: BtlePDUPayload.")
        self._payload = value

    @property
    def pdu_type(self):
        return self._pdu_type

    @pdu_type.setter
    def pdu_type(self, value):
        self._pdu_type = value


class ZigbeeMessage(Message):
    """Zigbee Specific Message Class.
    """

    def __init__(self, channel=None, **kwargs):
        super().__init__(ZIGBEE, **kwargs)

    @classmethod
    def fromraw(cls, raw_message, **kwargs):
        """Create a Zigbee specific message from either the raw bytes,  
        byte string, or a Scapy packet (which is assumed to be Dot15d4FCS) 

        TODO: Make a method to check for vulnerabilities + more than just the
        ZLL vulnerability. Older versions of zigbee, CVEs, etc.

        Arguments:
            raw_message [scapy.Packet, bytes, str] -- The scapy packet

        Returns:
            {Message} -- The formed message
        """
        if not raw_message:
            return False
        if not isinstance(raw_message, Packet):
            try:
                raw_message = Dot15d4FCS(raw_message)
            except:
                return False
        kwargs['rftap'] = {}
        vuln = {}
        if raw_message.haslayer(layers.rftap.RFtap):
            for field in raw_message[layers.rftap.RFtap].fields:
                if getattr(raw_message, field) is not None:
                    kwargs['rftap'][field] = getattr(raw_message, field)
        for pan_id_field in ['src_panid', 'dest_panid']:
            kwargs['pan'][pan_id_field] = Message.find_field(
                raw_message, pan_id_field)
        vuln['zll'] = True if raw_message.haslayer(layers.zigbee.ZLLScanResponse) else False
        m = ZigbeeMessage(
            sender=Message.find_field(raw_message, 'src_addr'),
            receiver=Message.find_field(raw_message, 'dest_addr'),
            seq_number=Message.find_field(raw_message, 'seqnum'),
            timestamp=Message.find_field(raw_message, 'time'),
            vuln=vuln,
            **kwargs,  # could contain channel info + number as well
        )
        return m
