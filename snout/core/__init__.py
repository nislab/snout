import logging

#from .device import *
#from .message import *


class LoggingCapability(object):
    """ Logging capability.
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            format='%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s')


class EventMgmtCapability(object):
    """ Event notification capability.

    Objects inheriting from this class will be able to emit events, and to
    subscribe to events by registering event handlers.
    """

    _handlers = {}

    def registerEventHandler(self, name, handler):
        self.__class__._handlers.setdefault(name, set()).add(handler)

    def deregisterEventHandler(self, name, handler):
        if name in self.__class__._handlers:
            if handler in self.__class__._handlers[name]:
                self.__class__._handlers[name].remove(handler)

    def emitEvent(self, event):
        handlers = set()
        # Consider handlers for this event
        handlers.update(self.__class__._handlers.get(event.name, set()))
        # Consider catch-all handlers for this protocol
        proto = event.name.split('.')[0]
        handlers.update(self.__class__._handlers.get(proto, set()))
        for handler in handlers:
            try:
                handler(*event.args, **event.kwargs)
            except TypeError as e:
                try:
                    logger = self.logger()
                except AttributeError:
                    logger = LoggingCapability().logger
                finally:
                    logger.error('Exception "%s" occurred when calling handler (%s -> %s) with args(%s) and kwargs(%s)'
                                 % (e, event.name, handler, event.args, event.kwargs))

                #    return False
        return True

    def eventName(self, proto, event):
        return "%s.%s" % (str(proto).strip().lower(), str(event).strip().lower())


class Event(object):
    """ The Event class used for the :class: EventMgmtCapability. 
    """

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs


class RequiredCapability(object):
    def __init__(self):
        super().__init__()
        self._required_attrs = []
        self._consider_children = []

    def reqs_satisfied(self):
        if not self._required_attrs and not self._consider_children:
            return True
        result = True
        for attr in self._required_attrs:
            result = result and bool(getattr(self, attr))
        if self._consider_children:
            for child in self._consider_children:
                obj = getattr(self, child)
                if obj and isinstance(obj, RequiredCapability):
                    result = result and obj.reqs_satisfied()
        return result

    def missing_reqs(self):
        result = []
        for attr in self._required_attrs:
            obj = getattr(self, attr)
            if not obj:
                result.append((self, self.__class__.__name__,attr))
        for child in self._consider_children:
            obj = getattr(self, child)
            if obj and isinstance(obj, RequiredCapability):
                result = result + obj.missing_reqs()
        return result
