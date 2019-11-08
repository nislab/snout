import json
import time
from enum import Enum
from pydoc import locate
from pprint import pprint

from snout.core import EventMgmtCapability, LoggingCapability
from snout.core.protocols import *

DEFAULT = 'default'
RAW = 'raw'
JSON = 'json'
SUMM = 'summary'

UITYPES = [
    DEFAULT,
    RAW,
    JSON,
    SUMM,
]


class UIType(Enum):
    raw = 1
    json = 2
    summary = 3

class UIController(EventMgmtCapability, LoggingCapability):

    _default_handlers = {
        BTLE: {
            DEFAULT: {
                'packet-received': 'snout.util.btle.BtleScanUIHandlerSummary',
            }
        }
    }

    def __init__(self, proto=None, ui_type=DEFAULT):
        super().__init__()
        self.proto = proto
        self.ui_type = ui_type
        self._initialized = False
        self.setup
        
        
    @property
    def initialized(self):
        return self._initialized
        
    @property
    def proto(self):
        return self._proto
    
    @proto.setter
    def proto(self, value):
        if value:
            if value in PROTO:
                self._proto = value
                self.setup()
            else:
                self.logger.warning('%s is not a valid protocol.', value)
        else:
            self.logger.warning('No protocol given.')

    @property
    def ui_type(self):
        return self._ui_type
    
    @ui_type.setter
    def ui_type(self, value):
        if value:
            if value in UITYPES:
                self._ui_type = value
                return
            else:
                self.logger.info('Unknown UI type "%s" given, using default instead.', value)
        else:
            self.logger.info('No UI type given, using default instead.')
        self._ui_type = DEFAULT


    def setup(self):
        if self.proto:
            handler = None
            if self.ui_type:
                self.logger.info("Setting up %s:%s handlers:", self.proto, self.ui_type)
                pdict = self.__class__._default_handlers.get(self.proto, None)
                if pdict:
                    handlers = pdict.get(self.ui_type, DEFAULT)
                    for event, handler_name in handlers.items():
                        handler_class = locate(handler_name)
                        handler = handler_class(self.proto)
                        eventname = self.eventName(self.proto, event)
            if not handler:
                self.logger.warning("No handler found. Reverting to %s:default handlers:", self.proto)
                handler = self.__class__.default_print_handler
                eventname = self.proto
            self.registerEventHandler(eventname, handler)
        else:
            self.logger.warning("No valid protocol given, cannot set up automatic UI handling.")

    @staticmethod
    def default_print_handler(*args, **kwargs):
        print("Default event handler:")
        pprint(args)
        pprint(kwargs)


class ScanUIHandler(LoggingCapability):
    def __init__(self, ui_type):
        super().__init__()
        self.type = ui_type
        self.packets = []
        self.update_interval = 0  # 0 = always update, otherwise interval in seconds
        self.last_update = 0

    def __call__(self, *args, **kwargs):
        self.logger.warning("Called (unimplemented) %s.__call__(args=%s, kwargs=%s)" % (self.__class__, args, kwargs))

    def check_update_ui(self):
        """Checks if the UI should be updated based off of self.update_interval
        and self.last_update

        Returns:
            {bool} -- True: should be updated, False: shouldn't be updated
        """
        return (time.time() - self.last_update - self.update_interval) > 0

    def updated_ui(self):
        """Updates self.last_update to be the current time. This should be called
        when the UI is updated.
        """
        self.last_update = time.time()
