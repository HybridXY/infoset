#!/usr/bin/env python3
"""Class interacts with CISCO-IETF-IP-MIB."""


import binascii
from snmp import Query
from collections import defaultdict


class Ipv6Query(Query):
    """Class interacts with CISCO-IETF-IP-MIB.

    Args:
        None

    Returns:
        None

    Key Methods:

        supported: Queries the device to determine whether the MIB is
            supported using a known OID defined in the MIB. Returns True
            if the device returns a response to the OID, False if not.

        layer3: Returns all needed layer 3 MIB information from the device.
            Keyed by OID's MIB name (primary key), IP address (secondary key).

    """

    def __init__(self, snmp_object):
        """Function for intializing the class.

        Args:
            snmp_object: SNMP Interact class object from snmp_manager.py

        Returns:
            None

        """
        # Define query object
        self.snmp_object = snmp_object

        # Get one OID entry in MIB (ipv6Forwarding)
        test_oid = '.1.3.6.1.2.1.55.1.1'

        super().__init__(snmp_object, test_oid, tags=['layer3'])

    def layer3(self):
        """Get layer 3 data from device.

        Args:
            None

        Returns:
            final: Final results

        """
        # Initialize key variables
        final = defaultdict(lambda: defaultdict(dict))

        # Get interface ifDescr data
        values = self.ipv6nettomediaphysaddress()
        for key, value in values.items():
            final['ipv6NetToMediaPhysAddress'][key] = value

        # Return
        return final

    def ipv6nettomediaphysaddress(self):
        """Return dict of the device's ipv6NetToMediaPhysAddress ARP table.

        Args:
            None

        Returns:
            data_dict: Dict of MAC addresses keyed by IPv6 Address

        """
        # Initialize key variables
        data_dict = defaultdict(dict)
        oid = '.1.3.6.1.2.1.55.1.12.1.2'

        # Get results
        results = self.snmp_object.swalk(oid, normalized=False)
        for key, value in results.items():
            # Get IP address, first 12 characters
            macaddress = binascii.hexlify(
                value).decode('utf-8')[0:12].lower()

            # Convert IP address from decimal to hex
            nodes = key.split('.')
            nodes_decimal = nodes[-16:]
            nodes_hex = []
            nodes_final = []
            for value in nodes_decimal:
                # Convert deximal value to hex,
                # then zero fill to ensure hex is two characters long
                hexbyte = ('%s') % (hex(int(value)))[2:]
                nodes_hex.append(hexbyte.zfill(2))

            # Convert to list of four byte hex numbers
            for pointer in range(0, len(nodes_hex) - 1, 2):
                fixed_value = ('%s%s') % (nodes_hex[pointer],
                                          nodes_hex[pointer + 1])
                nodes_final.append(fixed_value)

            # Create IPv6 string
            ipv6 = ':'.join(nodes_final)

            # Create ARP entry
            data_dict[ipv6] = macaddress.lower()

        # Return data
        return data_dict
