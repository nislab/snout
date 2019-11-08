# Advertising Data Type (AD Type) Definitions here:
# https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile
#

ad_types = {
    0x01:  	 {
        'name': "Flags",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.3 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.3 and 18.1 (v4.0)",
            "Core Specification Supplement, Part A, section 1.3",
        ]
    },
    0x02:  	 {
        'name': "Incomplete List of 16-bit Service Class UUIDs",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.1 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.1 and 18.2 (v4.0)",
            "Core Specification Supplement, Part A, section 1.1",
        ]
    },
    0x03:  	 {
        'name': "Complete List of 16-bit Service Class UUIDs",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.1 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.1 and 18.2 (v4.0)",
            "Core Specification Supplement, Part A, section 1.1",
        ]
    },
    0x04:  	 {
        'name': "Incomplete List of 32-bit Service Class UUIDs",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.1 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, section 18.2 (v4.0)",
            "Core Specification Supplement, Part A, section 1.1",
        ]
    },
    0x05:  	 {
        'name': "Complete List of 32-bit Service Class UUIDs",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.1 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, section 18.2 (v4.0)",
            "Core Specification Supplement, Part A, section 1.1",
        ]
    },
    0x06:  	 {
        'name': "Incomplete List of 128-bit Service Class UUIDs",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.1 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.1 and 18.2 (v4.0)",
            "Core Specification Supplement, Part A, section 1.1",
        ]
    },
    0x07:  	 {
        'name': "Complete List of 128-bit Service Class UUIDs" 	,
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.1 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.1 and 18.2 (v4.0)",
            "Core Specification Supplement, Part A, section 1.1",
        ]
    },
    0x08:  	 {
        'name': "Shortened Local Name",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.2 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.2 and 18.4 (v4.0)",
            "Core Specification Supplement, Part A, section 1.2",
        ]
    },
    0x09:  	 {
        'name': "Complete Local Name",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.2 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.2 and 18.4 (v4.0)",
            "Core Specification Supplement, Part A, section 1.2",
        ]
    },
    0x0A:  	 {
        'name': "Tx Power Level",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.5 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.5 and 18.3 (v4.0)",
            "Core Specification Supplement, Part A, section 1.5",
        ]
    },
    0x0D:  	 {
        'name': "Class of Device",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.6 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.5 and 18.5 (v4.0)",
            "Core Specification Supplement, Part A, section 1.6",
        ]
    },
    0x0E:  	 {
        'name': "Simple Pairing Hash C",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.6 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.5 and 18.5 (v4.0)",
        ]
    },
    0x0E:  	 {
        'name': "Simple Pairing Hash C-192",
        'reference': [
            "Core Specification Supplement, Part A, section 1.6",
        ]
    },
    0x0F:  	 {
        'name': "Simple Pairing Randomizer R",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.6 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.5 and 18.5 (v4.0)",
        ]
    },
    0x0F:  	 {
        'name': "Simple Pairing Randomizer R-192",
        'reference': [
            "Core Specification Supplement, Part A, section 1.6",
        ]
    },
    0x10:  	 {
        'name': "Device ID",
        'reference': [
            "Device ID Profile v1.3 or later",
        ]
    },
    0x10:  	 {
        'name': "Security Manager TK Value",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, sections 11.1.7 and 18.6 (v4.0)",
            "Core Specification Supplement, Part A, section 1.8",
        ]
    },
    0x11:  	 {
        'name': "Security Manager Out of Band Flags",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, sections 11.1.6 and 18.7 (v4.0)",
            "Core Specification Supplement, Part A, section 1.7",
        ]
    },
    0x12:  	 {
        'name': "Slave Connection Interval Range",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, sections 11.1.8 and 18.8 (v4.0)",
            "Core Specification Supplement, Part A, section 1.9",
        ]
    },
    0x14:  	 {
        'name': "List of 16-bit Service Solicitation UUIDs" 	,
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, sections 11.1.9 and 18.9 (v4.0)",
            "Core Specification Supplement, Part A, section 1.10",
        ]
    },
    0x15:  	 {
        'name': "List of 128-bit Service Solicitation UUIDs" 	,
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, sections 11.1.9 and 18.9 (v4.0)",
            "Core Specification Supplement, Part A, section 1.10",
        ]
    },
    0x16:  	 {
        'name': "Service Data",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, sections 11.1.10 and 18.10 (v4.0)",
        ]
    },
    0x16:  	 {
        'name': "Service Data - 16-bit UUID",
        'reference': [
            "Core Specification Supplement, Part A, section 1.11",
        ]
    },
    0x17:  	 {
        'name': "Public Target Address",
        'reference': [
            "Bluetooth Core Specification:Core Specification Supplement, Part A, section 1.13",
        ]
    },
    0x18:  	 {
        'name': "Random Target Address",
        'reference': [
            "Bluetooth Core Specification:Core Specification Supplement, Part A, section 1.14",
        ]
    },
    0x19:  	 {
        'name': "Appearance",
        'reference': [
            "Bluetooth Core Specification:Core Specification Supplement, Part A, section 1.12",
        ]
    },
    0x1A:  	 {
        'name': "Advertising Interval",
        'reference': [
            "Bluetooth Core Specification:Core Specification Supplement, Part A, section 1.15",
        ]
    },
    0x1B:  	 {
        'name': "LE Bluetooth Device Address",
        'reference': [
            "Core Specification Supplement, Part A, section 1.16",
        ]
    },
    0x1C:  	 {
        'name': "LE Role",
        'reference': [
            "Core Specification Supplement, Part A, section 1.17",
        ]
    },
    0x1D:  	 {
        'name': "Simple Pairing Hash C-256",
        'reference': [
            "Core Specification Supplement, Part A, section 1.6",
        ]
    },
    0x1E:  	 {
        'name': "Simple Pairing Randomizer R-256",
        'reference': [
            "Core Specification Supplement, Part A, section 1.6",
        ]
    },
    0x1F:  	 {
        'name': "List of 32-bit Service Solicitation UUIDs" 	,
        'reference': [
            "Core Specification Supplement, Part A, section 1.10",
        ]
    },
    0x20:  	 {
        'name': "Service Data - 32-bit UUID",
        'reference': [
            "Core Specification Supplement, Part A, section 1.11",
        ]
    },
    0x21:  	 {
        'name': "Service Data - 128-bit UUID",
        'reference': [
            "Core Specification Supplement, Part A, section 1.11",
        ]
    },
    0x22:  	 {
        'name': "LE Secure Connections Confirmation Value",
        'reference': [
            "Core Specification Supplement Part A, Section 1.6",
        ]
    },
    0x23:  	 {
        'name': "LE Secure Connections Random Value",
        'reference': [
            "Core Specification Supplement Part A, Section 1.6",
        ]
    },
    0x24:  	 {
        'name': "URI",
        'reference': [
            "Bluetooth Core Specification:Core Specification Supplement, Part A, section 1.18",
        ]
    },
    0x25:  	 {
        'name': "detailsoor Positioning",
        'reference': [
            "detailsoor Posiioning Service v1.0 or later",
        ]
    },
    0x26:  	 {
        'name': "Transport Discovery Data",
        'reference': [
            "Transport Discovery Service v1.0 or later",
        ]
    },
    0x27:  	 {
        'name': "LE Supported Features",
        'reference': [
            "Core Specification Supplement, Part A, Section 1.19",
        ]
    },
    0x28:  	 {
        'name': "Channel Map Update detailsication",
        'reference': [
            "Core Specification Supplement, Part A, Section 1.20",
        ]
    },
    0x29:  	 {
        'name': "PB-ADV",
        'reference': [
            "Mesh Profile Specification Section 5.2.1",
        ]
    },
    0x2A:  	 {
        'name': "Mesh Message",
        'reference': [
            "Mesh Profile Specification Section 3.3.1",
        ]
    },
    0x2B:  	 {
        'name': "Mesh Beacon",
        'reference': [
            "Mesh Profile Specification Section 3.9",
        ]
    },
    0x3D:  	 {
        'name': "3D Information Data",
        'reference': [
            "3D Synchronization Profile, v1.0 or later",
        ]
    },
    0xFF:  	 {
        'name': "Manufacturer Specific Data",
        'reference': [
            "Bluetooth Core Specification:Vol. 3, Part C, section 8.1.4 (v2.1 + EDR, 3.0 + HS and 4.0)Vol. 3, Part C, sections 11.1.4 and 18.11 (v4.0)",
            "Core Specification Supplement, Part A, section 1.4",
        ]
    },

}
