from snout.core.device import Device
from snout.core.message import Message
from snout.core.protocols import *


def test_device():
    d1 = Device.get_unique(BTLE, 'unique001')
    assert isinstance(d1, Device)
    d2 = Device.get_unique(BTLE, 'unique001')
    # get_unique ensures that devices with the same ID are the same object
    assert d1 == d2
    d3 = Device.get_unique(BTLE, 'unique002')
    assert d1 != d3


def test_device_bad():
    try:
        d1 = Device.get_unique('i_invented_this_protocol', 'unique003')
    except ValueError:
        d1 = None
    assert d1 is None


def test_device_update():
    d1 = Device.get_unique(BTLE, 'unique004')
    assert isinstance(d1.data, dict)
    assert not d1.data
    d1.update(something='text')
    assert 'text' == d1.data.get('something')
    d2 = Device.get_unique(BTLE, 'unique004a', foo='bar')
    assert d1 != d2
    assert 'bar' == d2.data.get('foo')


def test_message():
    d = Device.get_unique(BTLE, 'unique005')
    m = Message(BTLE, sender='unique005', payload='IMAMESSAGE')
    assert isinstance(m, Message)
    assert isinstance(m.sender, Device)
    assert m.sender == d
    assert len(d.messages_sent) == 1
    assert d.messages_sent[0] == m


def test_message_device_proto_mismatch():
    d = Device.get_unique(BTLE, 'unique006')
    d2 = Device.get_unique(BTLE, 'unrelatedBystander')
    m = Message(WIFI, sender='unique006', payload='IMAMESSAGE')
    assert isinstance(m, Message)
    assert isinstance(m.sender, Device)
    assert m.sender != d
    assert len(m.sender.messages_sent) == 1
    assert len(d.messages_sent) == 0
    assert len(d2.messages_sent) == 0
