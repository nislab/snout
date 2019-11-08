# File: advertising.py
# Original Author:  Johannes K Becker <jkbecker@bu.edu>, 2019-01-29-
# Revised by: Simson Garfinkel <simsong@acm.org> 2019-07-19-
# See also: https://github.com/simsong/python-corebluetooth/

import codecs
import json

from .assigned_numbers import *
from snout.core.protocols import BTLE

RAW = 'raw'
HEX = 'hex'
FLAGS = 'flags'
SEC_MG_OOB_FLAGS = 'sec-mg-oob-flags'
SERVICE_DATA = 'service-data'
MANUFACTURER_SPECIFIC = 'manufacturer-specific'
UNKNOWN = 'unknown'
COMPANY_ID = 'company_id'
COMPANY_NAME = 'company_name'
COMPANY_RAW  = 'company_raw'
IBEACON='ibeacon'

FLAG_LEL = 'LE Limited Discoverable Mode'
FLAG_LEG = 'LE General Discoverable Mode'
FLAG_BR  = 'BR/EDR Not Supported (i.e. bit 37 of LMP Extended Feature bits Page 0)'
FLAG_SLEBR = 'Simultaneous LE and BR/EDR to Same Device Capable (Controller) (i.e. bit 49 of LMP Extended Feature bits Page 0)'
FLAG_LEBRS = 'Simultaneous LE and BR/EDR to Same Device Capable (Host) (i.e. bit 66 of LMP Extended Feature bits Page 1)'

FLAG_OOB = "OOB data present"
FLAG_NO_OOB = "OOB data not present"
FLAG_LE  = "LE supported (Host) (i.e. bit 65 of LMP Extended Feature bits Page 1"
FLAG_LE_BR = "Simultaneous LE and BR/EDR to Same Device Capable (Host) (i.e. bit 66 of LMP Extended Fea- ture bits Page 1"
FLAG_RANDOM_ADDRESS = "Address Type: Random Address"
FLAG_PUBLIC_ADDRESS = "Address Type: Public Address"

APPLE_DATA_TYPES = {
    0x02: 'iBeacon',
    0x05: 'AirDrop',
    0x07: 'AirPods',
    0x09: 'AirPlay Destination',
    0x0a: 'AirPlay Source',
    0x0c: 'Handoff',
    0x0d: 'Wi-Fi Settings',
    0x0e: 'Instant Hotspot',
    0x0f: 'Wi-Fi Join Network',
    0x10: 'Nearby',
}

APPLE_ACTION_CODES = {
    1:  "iOS recently updated",
    3:  "Locked Screen",
    7:  "Transition Phase",
    10: "Locked Screen, Inform Apple Watch",
    11: "Active User",
    13: "Unknown",
    14: "Phone Call or Facetime",
}


def word16be(data):
    """return data[0] and data[1] as a 16-bit Big Ended Word"""
    return (data[1] << 8) | data[0]


class AbstractContextManager():
    def __init__(self, buf):
        assert type(buf) == bytes
        self.buf = buf
        self.pos = 0

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return


class AdvDataParser(AbstractContextManager):
    """ Returns a context manager. Given a buffer representing BLE AdvData,
    return a series of (AD Structure) fields. Assumes that data contains a
    set of (length,data) fields.
    """

    def get_ad_structure(self, lensize=1):
        while self.pos < len(self.buf):
            try:
                ad_len = self.buf[self.pos]
                ad_data = self.buf[self.pos+1:self.pos+ad_len+1]
                self.pos += 1 + ad_len
                yield ad_data
            except IndexError as e:
                pass

class AppleTypeParser(AbstractContextManager):
    """ Returns a context manager. Given a buffer, return a series of
    (type,data) fields. Assumes that data contains a set of
    (type,length,data) fields used by Apple, where (type) and (length)
    are both unsigned 8-bit values.
    """

    def get_type_data(self, lensize=1):
        while self.pos < len(self.buf):
            try:
                ad_type = self.buf[self.pos]
                ad_len = self.buf[self.pos+1]
                ad_data = self.buf[self.pos+2:self.pos+ad_len+2]
                self.pos += 2 + ad_len
                yield (ad_type, ad_data)
            except IndexError as e:
                pass

class BtlePDUPayload(object):
    def __init__(self, adv_data=bytes(), manuf_data=bytes()):
        self.d = {}
        self.d[HEX] = adv_data.hex()

        with AdvDataParser(adv_data) as lr:
            for ad_structure in lr.get_ad_structure():
                self.parse_ad_structure(ad_structure)

        if manuf_data:
            self.parse_ad_type_0xff(manuf_data)

    @classmethod
    def fromstring(cls, adv_data_string):
        return BtlePDUPayload(codecs.decode(adv_data_string, 'hex'))

    def __repr__(self):
        return f"BtlePDUPayload<{self.d}>"

    def json(self, indent=4):
        return json.dumps(self.d, indent=indent)

    def dict(self):
        return self.d

    def parse_ad_structure(self, data):
        """Parse the advertising structure for BTLE packets
        
        Arguments:
            data {bytes} -- The data to parse
        """
        AD_TYPE_PARSERS = {
            0x01: self.parse_ad_type_0x01,
            0x06: self.parse_ad_type_0x06,
            0x11: self.parse_ad_type_0x11,
            0x16: self.parse_ad_type_0x16,
            0xff: self.parse_ad_type_0xff,
        }
        if data:
            ad_type = data[0]
            ad_data = data[1:]
            if ad_type in AD_TYPE_PARSERS:
                AD_TYPE_PARSERS[ad_type](ad_data)
            else:
                self.d[UNKNOWN] = {'type': ad_type, 'hex': ad_data.hex()}

    def parse_ad_type_0x01(self, data):
        """ Implementation of Bluetooth Specification Version 4.0 [Vol 3] Table 18.1: Flags
        """
        ad_flags = []
        val = data[0]
        if val & 0x01 << 0:
            ad_flags.append(FLAG_LEL)
        if val & 0x01 << 1:
            ad_flags.append(FLAG_LEG)
        if val & 0x01 << 2:
            ad_flags.append(FLAG_BR)
        if val & 0x01 << 3:
            ad_flags.append(FLAG_SLEBR)
        if val & 0x01 << 4:
            ad_flags.append(FLAG_LEBRS)
        self.d[FLAGS] = ad_flags

    def parse_ad_type_0x06(self, data):
        """ TODO: This should be endian-reversed and converted to str.
        """
        self.d[ad_types[0x06]['name']] =  data.hex()

    def parse_ad_type_0x11(self, data):
        """ Implementation of Bluetooth Specification Version 4.0 [Vol 3] 
        Table 18.7: Security Manager OOB Flags
        """
        val = data[0]
        ad_flags = []
        if val & 0x01 << 0:
            ad_flags.append(FLAG_OOB)
        else:
            ad_flags.append(FLAG_NO_OOB)
        if val & 0x01 << 1:
            ad_flags.append(FLAG_LE)
        if val & 0x01 << 2:
            ad_flags.append(FLAG_LE_BR)
        if val & 0x01 << 3:
            ad_flags.append(FLAG_RANDOM_ADDRESS)
        else:
            ad_flags.append(FLAG_PUBLIC_ADDRESS)
        self.d[SEC_MG_OOB_FLAGS] = ad_flags

    def parse_ad_type_0x16(self, data):
        """Implementation of Bluetooth Specification Version 4.0 [Vol 3]
            Table 18.10: Service Data and GATT Services list
            https://www.bluetooth.com/specifications/gatt/services
        """
        service_uuid = word16be(data[0:2])
        service_data = data[2:]
        self.d[SERVICE_DATA] = {'uuid': service_uuid, 'data': service_data}

    def parse_ad_type_0xff(self, data):
        """Implementation of Bluetooth Specification Version 4.0 [Vol 3]
            Table 18.11: Manufacturer Specific Data and Company
            Identifier List:
            https://www.bluetooth.com/specifications/assigned-numbers/company-identifiers
        """
        # First 2 octets contain the 16 bit service UUID, flip bytes around
        company_id = word16be(data[0:2])

        man_data = data[2:]

        self.d[COMPANY_ID] = company_id
        self.d[COMPANY_RAW] = man_data.hex()
        self.d[COMPANY_NAME] = company_ids.get(company_id, '??')

        AD_MAN_PARSERS = {
            0x0006: self.parse_man_data_microsoft,
            0x004C: self.parse_man_data_apple,
        }
        if company_id in AD_MAN_PARSERS:
            self.d[MANUFACTURER_SPECIFIC] = AD_MAN_PARSERS[company_id](
                man_data)

    def parse_man_data_apple(self, man_data):
        """Parses the apple manufacturer data
        
        Arguments:
            man_data {bytes} -- BTLE message bytes where the manufacturer data is stored
        
        Returns:
            {dict} -- The manufacturer data
        """
        d = []
        with AppleTypeParser(man_data) as tr:
            for (apple_type, apple_data) in tr.get_type_data():
                if apple_type in APPLE_DATA_TYPES:
                    record = {'type': APPLE_DATA_TYPES.get(apple_type)}
                    if apple_type == 0x0c:  # Handoff
                        record['Clipboard Status'] = apple_data[0]
                        record['Sequence Number'] = word16be(apple_data[1:3])
                    elif apple_type == 0x0d:  # Wi-Fi Settings
                        record['iCloud ID'] = apple_data[2:].hex()
                    elif apple_type == 0x0e:  # Instant Hotspot
                        try:
                            record['Battery Life'] = apple_data[4]
                        except IndexError:
                            pass
                        try:
                            record['Cell Service'] = apple_data[6]
                        except IndexError:
                            pass
                        try:
                            record['Cell Bars'] = apple_data[7]
                        except IndexError:
                            pass
                    elif apple_type == 0x0f:  # Wi-Fi Join Network
                        record['data'] = apple_data.hex()
                    elif apple_type == 0x10:  # Nearby
                        record['Location Sharing'] = apple_data[0] >> 4
                        record['Action Code'] = apple_data[0] & 0x0f
                        record['Action Code Text'] = APPLE_ACTION_CODES.get(
                            record['Action Code'], '??')
                        nearby_data = apple_data[1:]
                        if len(nearby_data) == 1 and nearby_data[0] == 0x00:
                            record['iOS Version Hint'] = '10'
                        if len(nearby_data) == 4:
                            record['Data'] = nearby_data[1:]
                            if nearby_data[0] == 0x10:
                                record['iOS Version Hint'] = '11'
                            if nearby_data[0] in [0x18, 0x1c]:
                                record['iOS Version Hint'] = '12'
                                record['Wi-Fi'] = 'On' if nearby_data[0] == 0x1c else 'Off'

                        #print(" NEARBY <%s> len=%d | action=%d (%s)" % (nearby_data.hex(),len(nearby_data), record['Action Code'], record['Action Code Text']), end='')
                        #print("    byte1=%x    byte2=%x    byte3=%x    byte4=%x" % (
                        #    nearby_data[0],
                        #    nearby_data[1] if len(nearby_data) > 1 else -1,
                        #    nearby_data[2] if len(nearby_data) > 1 else -1,
                        #    nearby_data[3] if len(nearby_data) > 1 else -1,
                        #))
                else:
                    record = {'type': hex(apple_type),
                              'data': apple_data.hex()}
                d.append(record)
        return d

    def parse_man_data_microsoft(self, man_data):
        """Parses the microsoft manufacturer data
        
        TODO: More in depth Microsoft Parsing

        Arguments:
            man_data {bytes} -- BTLE message bytes where the manufacturer data is stored
        
        Returns:
            {dict} -- The manufacturer data
        """
        return man_data.hex()
