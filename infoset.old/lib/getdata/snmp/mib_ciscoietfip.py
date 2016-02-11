#!/usr/bin/env python3
"""Class interacts with CISCO-IETF-IP-MIB."""


import binascii
from collections import defaultdict


# Import project libraries
from getdata.snmp import snmp_manager


class Query(object):

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

    def __init__(self, snmp_params):
        """Function for intializing the class.

        Args:
            snmp_params: SNMP parameters for querying the host

        Returns:
            None

        """
        # Define query object
        self.snmp_query = snmp_manager.Interact(snmp_params)

    def supported(self):
        """Return device's support for the MIB.

        Args:
            None

        Returns:
            validity: True if supported

        """
        # Support OID
        validity = False

        # Get one OID entry in MIB (cInetNetToMediaPhysAddress)
        oid = '.1.3.6.1.4.1.9.10.86.1.1.3.1.3'

        # Return nothing if oid doesn't exist
        if self.snmp_query.oid_exists(oid) is True:
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

        # Get interface cInetNetToMediaPhysAddress data
        values = self.cinetnettomediaphysaddress()
        for key, value in values.items():
            final['cInetNetToMediaPhysAddress'][key] = value

        # Return
        return final

    def cinetnettomediaphysaddress(self):
        """Return dict of the device's ARP table.

        Args:
            None

        Returns:
            data_dict: Dict of MAC addresses keyed by IPv6 Address

        """
        # Initialize key variables
        data_dict = defaultdict(dict)
        oid = '.1.3.6.1.4.1.9.10.86.1.1.3.1.3'

        # Get results
        results = self.snmp_query.swalk(oid, normalized=False)
        for key, value in sorted(results.items()):
            # Get IP address, first 12 characters
            macaddress = binascii.hexlify(
                value).decode('utf-8')[0:12].lower()

            # Convert IP address from decimal to hex
            nodes = key.split('.')
            ipv6decimal = nodes[-16:]
            ipv6hex = []
            for value in ipv6decimal:
                # Convert deximal value to hex,
                # then zero fill to ensure hex is two characters long
                hexbyte = ('%s') % (hex(int(value)))[2:]
                ipv6hex.append(hexbyte.zfill(2))

            # Create IPv6 string
            ipv6 = ':'.join(ipv6hex)

            # Create ARP entry
            data_dict[ipv6] = macaddress.lower()

        # Return data
        return data_dict
