from snout.core import EventMgmtCapability, LoggingCapability, RequiredCapability
from snout.core.config import Config as cfg
from snout.core.protocols import PROTO
from snout.core.radio import Radio, SDRController
from snout.core.ui import UIController


class Snout(LoggingCapability, EventMgmtCapability, RequiredCapability):

    def __init__(self, **kwargs):
        # Initialize parent classes
        super().__init__()
        self._required_attrs = ['hardware', 'protocol', 'env', 'subcommand']
        self._consider_children = ['ui', 'radio', 'sdrcontroller']

        self.automatic = kwargs.pop('automatic', False)
        self.filename = kwargs.pop('filename', None)
        self.wireshark = kwargs.pop('wireshark', None)
        self.display = kwargs.pop('display', False)

        # Set up UI
        self.ui = UIController()


        # Get PyBOMBS environment from config
        self.env = kwargs.pop('env', cfg.pybombs_env())

        # Set up Radio
        self.hardware = kwargs.pop('hardware', None)
        if self.hardware:
            self.radio = Radio(hardware=self.hardware, detect=False, env=self.env)
        else:
            self.radio = Radio(detect=True, env=self.env)
            self.hardware = self.radio.hardware

        self.protocol = kwargs.pop('protocol', None)

        # Set up SDR Controller
        self.subcommand = kwargs.pop('subcommand', None)
        self.sdrcontroller = SDRController(radio=self.radio)

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, value):
        if value:
            if value in PROTO:
                self._protocol = value
                self.ui.proto = self._protocol
            else:
                raise ValueError(
                    "Protocol '%s' is not an allowed value (%s)." % (value, PROTO))
        else:
            self._protocol = None
        if self.radio:
            print(self._protocol, self.radio.protocols.keys())
            if not self._protocol in self.radio.protocols.keys():
                self.logger.warning("Radio hardware not compatible with desired protocol. Please specify compatible hardware using the --hardware option.")

    @property
    def hardware(self):
        return self._hardware
    
    @hardware.setter
    def hardware(self, value):
        self._hardware = value