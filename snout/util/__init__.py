from snout.core.protocols import *

# Default Timeout values
default_timeouts = {
    BTLE:      10,
    WIFI:      30,
    ZIGBEE:    10,
    ZWAVE:     10,
}

# Default Channel values (low, high, default)
default_channels = {
    BTLE:      (0, 39, 37),
    WIFI:      (1, 11, 6),
    ZIGBEE:    (11, 26, 11),
    ZWAVE:     (865.0, 926.0, 908.4), # special case...zwave is country dependent and doesn't use channels
}
