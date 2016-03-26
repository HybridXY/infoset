#!/usr/bin/env python3
"""Class interacts with devices supporting IP-MIB."""


from collections import defaultdict
import binascii

from infoset.snmp.base_query import Query


def get_query():
    """Return this module's Query class."""
    return IpQuery


def init_query(snmp_object):
    """Return initialize and return this module's Query class."""
    return IpQuery(snmp_object)


class IpQuery(Query):
    """Class interacts with devices supporting IP-MIB.

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

        super().__init__(snmp_object, '', tags=['layer3'])

    def supported(self):
        """Return device's support for the MIB.

        Args:
            None

        Returns:
            validity: True if supported

        """
        # Support OID
        validity = True

        # Return
        return validity

    def layer3(self):
        """Get layer 3 data from device.

        Args:
            None

        Returns:
            final: Final results

        """
        # Initialize key variables
        final = defaultdict(lambda: defaultdict(dict))

        # Get interface ipNetToMediaTable data
        values = self.ipnettomediatable()
        for key, value in values.items():
            final['ipNetToMediaTable'][key] = value

        # Get interface ipNetToPhysicalPhysAddress data
        values = self.ipnettophysicalphysaddress()
        for key, value in values.items():
            final['ipNetToPhysicalPhysAddress'][key] = value

        # Return
        return final

    def ipnettomediatable(self):
        """Return dict of ipNetToMediaTable, the device's ARP table.

        Args:
            None

        Returns:
            data_dict: Dict of MAC addresses keyed by IPv4 address

        """
        # Initialize key variables
        data_dict = {}

        # Process
        oid = '.1.3.6.1.2.1.4.22.1.2'
        results = self.snmp_object.walk(oid, normalized=False)
        for key, value in results.items():
            # Determine IP address
            nodes = key.split('.')
            octets = nodes[-4:]
            ipaddress = '.'.join(octets)

            # Determine MAC address
            macaddress = binascii.hexlify(value).decode('utf-8')

            # Create ARP table entry
            data_dict[ipaddress] = macaddress.lower()

        # Return data
        return data_dict

    def ipnettophysicalphysaddress(self):
        """Return dict of the device's ipNetToPhysicalPhysAddress ARP table.

        Args:
            None

        Returns:
            data_dict: Dict of MAC addresses keyed by IPv6 Address

        """
        # Initialize key variables
        data_dict = {}
        oid = '.1.3.6.1.2.1.4.35.1.4'

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
