import timeago
from datetime import datetime as dt

from snout.core.protocols import *
from snout.core.protocols.btle import assigned_numbers as btle_an


class DuplicateDeviceException(ValueError):
    def __init__(self, protocol, did):
        device = Device.known(protocol, did)
        self.message = f"Duplicate device. {protocol} Device ID '{did}' already exists ({device})."


class Device(object):
    instances = {k: [] for k in PROTO}

    @classmethod
    def known(cls, protocol, did):
        """Checks if a device is known based on the protocol and device ID (did)
        
        Arguments:
            protocol {str} -- The protocol of the device in question
            did {str} -- The device ID string
        
        Returns:
            [Device] -- The device if it is known, otherwise False
        """
        type_instances = cls.instances.get(protocol, {})
        for i in type_instances:
            if did in i.ids:
                return i
        return False

    @classmethod
    def get_unique(cls, protocol, did, **kwargs):
        """Gets a unique device given a device id and protocol.

        If the device is known, then the known device is returned.
        Otherwise, a new device is created with the respective
        protocol and device ID
        
        Arguments:
            protocol {str} -- The protocol to find a unique device for
            did {str} -- The device ID string
        
        Returns:
            Device -- The unique device respective to the protocol and device ID
        """
        if isinstance(did, Device) and protocol == did.protocol:
            did.update(**kwargs)
            return did
        known_device = cls.known(protocol, did)
        if known_device:
            known_device.update(**kwargs)
            return known_device
        else:
            return Device(protocol, did, **kwargs)

    def __init__(self, protocol, did, **kwargs):
        self.protocol = protocol
        self._ids = [did]
        self._messages_sent = []
        self._messages_received = []
        self._data = {}
        self._vuln = {}
        if Device.known(protocol, did):
            raise DuplicateDeviceException(protocol, did)
        self.update(**kwargs)

        # Add device to known devices
        Device.instances[protocol].append(self)

    @property
    def ids(self):
        return self._ids

    @property
    def id(self):
        return self._ids[-1]

    @property
    def vuln(self):
        return self._vuln

    @vuln.setter
    def vuln(self, value):
        self._vuln = value

    @id.setter
    def id(self, value):
        try:
            self._ids.append(value)
        except AttributeError:
            self._ids = [value]

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, value):
        if value not in PROTO:
            raise ValueError("Protocol {protocol} is not recognized by Snout.")
        self._protocol = value

    def update(self, **kwargs):
        self.data = kwargs

    @property
    def messages_sent(self):
        return self._messages_sent

    @property
    def messages_received(self):
        return self._messages_received

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        try:
            if isinstance(value, dict):
                self._data.update(value)
            else:
                raise TypeError('Data must be set with a dictionary')
        except AttributeError:
            self._data = value

    @property
    def last_seen(self):
        if len(self.messages_sent) > 0:
            return self.messages_sent[-1].timestamp
        return 0

    @property
    def last_seen_nice(self):
        if len(self.messages_sent) > 0:
            return timeago.format(dt.fromtimestamp(self.last_seen), dt.now())
        return 0

    @property
    def occurrences(self):
        return len(self.messages_sent)

    @property
    def uptime(self):
        if len(self.messages_sent) > 0:
            return round(self.messages_sent[-1].timestamp - self.messages_sent[0].timestamp)
        return -1

    @property
    def uptime_nice(self):
        """Formats the uptime into a nice and readable string
        
        Returns:
            str -- The time string if uptime >= 0, otherwise "-"
        """
        uptime = self.uptime
        if uptime >= 0:
            nice = "%02d:%02d" % (uptime/60, uptime % 60)
            if uptime > 60*60:
                hours = int(uptime/(60*60))
                nice = "%02d:%02d:%02d" % (
                    uptime/(60*60), (uptime-hours)/60, (uptime-hours) % 60)
            return nice
        return '-'

    @property
    def vendor(self):
        """Finds the vendor based on properties of the messages sent by the device
        
        TODO: Specific vendor finding methods for each protocol 

        Returns:
            str -- the vendor name if known, otherwise "-"
        """
        for m in self.messages_sent:
            if m.protocol == BTLE:
                company_name = m.payload.d.get('company_name', None)
                if company_name:
                    return company_name
                # Fitbit
                # TODO: This is messy and should be redone. See #39.
                fitbit_hint = m.payload.d.get(
                    btle_an.ad_types[0x06]['name'], None)
                if fitbit_hint and 'ba5689a6fabfa2bd01467d6e00fbabad' in fitbit_hint:
                    return "FitBit"
        return '-'

    def fingerprint_vendor(self):
        """ Guesstimating the vendor based on indirect clues.
        """
        if self.protocol == BTLE:
            for p in self.messages_sent:
                if 'company_name' in p:
                    return p['company_name']
                # TODO: This is messy and should be redone. See #39.
                if btle_an.ad_types[0x06]['name'] in p:
                    if 'ba5689a6fabfa2bd01467d6e00fbabad' in p[btle_an.ad_types[0x06]['name']]:
                        return "FitBit"
        return False

    @property
    def model(self):
        """Finds the model based on properties of the messages sent by the device

        TODO: Specific model finding methods for each protocol 
        
        Returns:
            The model of the device in known, otherwise "-"
        """
        for m in self.messages_sent:
            if m.protocol == BTLE:
                # Fitbit
                # TODO: This is messy and should be redone. See #39.
                fitbit_hint = m.payload.d.get(
                    btle_an.ad_types[0x06]['name'], None)
                if fitbit_hint and 'ba5689a6fabfa2bd01467d6e00fbabad' in fitbit_hint:
                    return "Charge / Charge HR"
                company_id = m.payload.d.get('company_id', None)
                man_data = m.payload.d.get('manufacturer-specific', None)
                if company_id == 0x004c and man_data:
                    for record in man_data:
                        if record.get('type', '') == 'AirPods':
                            return 'AirPods'
        return '-'

    @property
    def os(self):
        """Finds the OS based on properties of the messages sent by the device

        TODO: Specific OS finding methods for each protocol 
        
        Returns:
            The OS of the device in known, otherwise "-"
        """
        for m in self.messages_sent:
            if m.protocol == BTLE:
                company_id = m.payload.d.get('company_id', None)
                man_data = m.payload.d.get('manufacturer-specific', None)
                if company_id == 0x004c and man_data:
                    for record in man_data:
                        if record.get('type', '') == 'Nearby':
                            hint = record.get('iOS Version Hint', False)
                            return 'iOS '+hint if hint else '-'
                if company_id == 0x0006:
                    # https://docs.microsoft.com/en-us/uwp/api/windows.devices.bluetooth.advertisement.bluetoothleadvertisementpublisher
                    return 'Windows 10 >= v10.0.10240.0'
        return '-'

    def fingerprint_os(self):
        """ Guesstimating the vendor based on indirect clues.
        """
        if self.protocol == BTLE:
            for p in self.messages_sent:
                if 'manufacturer-specific' in p and 'company_id' in p:
                    if p['company_id'] == 0x004c:
                        for record in p['manufacturer-specific']:
                            if record.get('type', '') == 'Nearby':
                                hint = record.get('iOS Version Hint', False)
                                return 'iOS '+hint if hint else False
        return False

    @property
    def activity(self):
        """Finds the device activity based on properties of the messages sent by the device

        TODO: Specific activity finding methods for each protocol 
        TODO: Activity Prioritization
        
        Returns:
            The activity of the device in known, otherwise "-"
        """
        activities = []
        for m in self.messages_sent:
            if m.protocol == BTLE:
                man_data = m.payload.d.get('manufacturer-specific', None)
                if man_data:
                    for record in man_data:
                        if isinstance(record, dict) and record.get('type', '') == 'Nearby':
                            hint = record.get('Action Code Text', False)
                            if hint:
                                activities.append(
                                    (timeago.format(dt.fromtimestamp(m.timestamp), dt.now()), hint))
        activities_unique = []
        prev_a = ''
        for t, a in activities:
            if a != prev_a:
                prev_a = a
                activities_unique.append( (t, a) )
        while len(activities_unique)>3:
            activities_unique.pop(0)
        return ', '.join([f"{t}: {a}" for t, a in activities_unique]) if activities_unique else '-'
