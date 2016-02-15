#!/usr/bin/env python3
"""Class for normalizing the data read from YAML files."""

import os
import yaml


import jm_general


class Translator(object):
    """Process configuration file for a host.

    The aim of this class is to process the YAML file consistently
    across multiple manufacturers and present it to other classes
    consistently. That way manufacturer specific code for processing YAML
    data is in one place.

    For example, there isn’t a standard way of reporting ethernet duplex
    values with different manufacturers exposing this data to different MIBs.
    The jm_xlate file attempts to determine the true duplex value of the
    device by testing the presence of one or more OID values in the data.
    It adds a ‘duplex’ data key to self.ports to act as the canonical key for
    duplex across all devices.

    """

    def __init__(self, config, host, ifindices=None):
        """Initialize class.

        Args:
            config: Configuration file object
            host: Hostname to process
            ifindices: List of ifindices to process

        Returns:
            data_dict: Dict of summary data

        Summary:

            IF-MIB

            A significant portion of this code relies on ifIndex
            IF-MIB::ifStackStatus information. This is stored under the
            'system' key of the device YAML files.

            According to the official IF-MIB file. ifStackStatus is a
            "table containing information on the relationships
            between the multiple sub-layers of network interfaces.  In
            particular, it contains information on which sub-layers run
            'on top of' which other sub-layers, where each sub-layer
            corresponds to a conceptual row in the ifTable.  For
            example, when the sub-layer with ifIndex value x runs over
            the sub-layer with ifIndex value y, then this table
            contains:

              ifStackStatus.x.y=active

            For each ifIndex value, I, which identifies an active
            interface, there are always at least two instantiated rows
            in this table associated with I.  For one of these rows, I
            is the value of ifStackHigherLayer; for the other, I is the
            value of ifStackLowerLayer.  (If I is not involved in
            multiplexing, then these are the only two rows associated
            with I.)

            For example, two rows exist even for an interface which has
            no others stacked on top or below it:

              ifStackStatus.0.x=active
              ifStackStatus.x.0=active"

            In the case of Juniper equipment, VLAN information is only
            visible on subinterfaces of the main interface. For example
            interface ge-0/0/0 won't have VLAN information assigned to it
            directly.

            When a VLAN is assigned to this interface, a subinterface
            ge-0/0/0.0 is automatically created with a non-Ethernet ifType.
            VLAN related OIDs are only maintained for this new subinterface
            only. This makes determining an interface's VLAN based on
            Ethernet ifType more difficult. ifStackStatus maps the ifIndex of
            the primary interface (ge-0/0/0) to the ifIndex of the secondary
            interface (ge-0/0/0.0) which manages higher level protocols and
            data structures such as VLANs and LLDP.

            The primary interface is referred to as the
            ifStackLowerLayer and the secondary subinterface is referred to
            as the ifStackHigherLayer.

            =================================================================

            Layer1 Keys

            The following Layer1 keys are presented by the ethernet_data
            method due to this instantiation:

            jm_vlan: A list of vendor agnostic VLANs
            jm_trunk: A vendor agnostic flag of "True" if the port is a Trunk
            jm_duplex: A vendor agnostic status code for the duplex setting

        """
        # Initialize key variables
        self.ports = {}
        yaml_file = config.snmp_device_file(host)

        # Fail if yaml file doesn't exist
        if os.path.isfile(yaml_file) is False:
            log_message = (
                'YAML file %s for host %s doesn\'t exist! '
                'Try polling devices first.') % (yaml_file, host)
            jm_general.logit(1017, log_message)

        # Read file
        with open(yaml_file, 'r') as file_handle:
            yaml_from_file = file_handle.read()
        yaml_data = yaml.load(yaml_from_file)

        # Create dict for layer1 Ethernet data
        for ifindex, metadata in yaml_data['layer1'].items():
            # Only process if ifIndex is found in ifindices
            if ifindices is not None:
                if int(ifindex) not in ifindices:
                    continue

            # Process metadata
            if _is_ethernet(metadata) is True:
                # Get the ifIndex of the lower layer interface
                ifstacklowerlayer = ifindex

                # Determine the ifIndex for any existing higher
                # layer subinterfaces whose data could be used
                # for upper layer2 features such as VLANs and
                # LAG trunking
                higherlayers = yaml_data[
                    'system']['IF-MIB'][ifstacklowerlayer]
                for higherlayer in higherlayers.keys():
                    if higherlayer == '0':
                        ifstackhigherlayer = ifstacklowerlayer
                    else:
                        ifstackhigherlayer = higherlayer
                    break

                # Update vlan to universal infoset metadata value
                metadata['jm_vlan'] = _vlan(yaml_data, ifstackhigherlayer)

                # Update trunk status to universal infoset metadata value
                metadata['jm_trunk'] = _trunk(yaml_data, ifstackhigherlayer)

                # Update duplex to universal infoset metadata value
                metadata['jm_duplex'] = _duplex(metadata)

                # Update ports
                self.ports[int(ifindex)] = metadata

        # Get system
        self.system = yaml_data['system']

    def system_summary(self):
        """Return system summary data.

        Args:
            None

        Returns:
            data_dict: Dict of summary data

        """
        # Initialize key variables
        data_dict = {}

        # Assign system variables
        v2mib = self.system['SNMPv2-MIB']
        for key in v2mib.keys():
            data_dict[key] = v2mib[key]['0']

        # Return
        return data_dict

    def ethernet_data(self):
        """Return L1 data for Ethernet ports only.

        Args:
            None

        Returns:
            self.ports: L1 data for Ethernet ports

        """
        return self.ports


def _is_ethernet(metadata):
    """Return whether ifIndex metadata belongs to an Ethernet port.

    Args:
        metadata: Data dict related to the port

    Returns:
        valid: True if valid ethernet port

    """
    # Initialize key variables
    valid = False

    # Process ifType
    if 'ifType' in metadata:
        # Get port name
        name = metadata['ifName'].lower()

        # Process ethernet ports
        if metadata['ifType'] == 6:
            # VLAN L2 VLAN interfaces passing as Ethernet
            if name.startswith('vl') is False:
                valid = True

    # Return
    return valid


def _vlan(metadata, ifindex):
    """Return vlan for specific ifIndex.

    Args:
        metadata: Data dict related to the device
        ifindex: ifindex in question

    Returns:
        vlans: VLAN numbers as a list

    """
    # Initialize key variables
    vlans = None

    # Determine vlan number for Cisco devices
    if 'vmVlan' in metadata['layer1'][ifindex]:
        vlans = [int(metadata['layer1'][ifindex]['vmVlan'])]

    # Determine vlan number for Juniper devices
    if 'jnxExVlanTag' in metadata['layer1'][ifindex]:
        tags = metadata['layer1'][ifindex]['jnxExVlanTag']
        if bool(tags) is True:
            vlans = tags

    # Return
    return vlans


def _duplex(metadata):
    """Return duplex value for port.

    Args:
        metadata: Data dict related to the port

    Returns:
        duplex: Duplex value
            0) Unknown
            1) Half
            2) Full
            3) Half Auto
            4) Full Auto

    """
    # Initialize key variables
    duplex = 0

    # Process swPortDuplexStatus
    if 'swPortDuplexStatus' in metadata:
        value = metadata['swPortDuplexStatus']

        # Process duplex
        if value == 1:
            duplex = 2
        else:
            duplex = 1

    # Process dot3StatsDuplexStatus
    elif 'dot3StatsDuplexStatus' in metadata:
        value = metadata['dot3StatsDuplexStatus']

        # Process duplex
        if value == 2:
            duplex = 1
        elif value == 3:
            duplex = 2

    # Process portDuplex
    elif 'portDuplex' in metadata:
        value = metadata['portDuplex']

        # Process duplex
        if value == 1:
            duplex = 1
        elif value == 2:
            duplex = 2

    # Process c2900PortDuplexState
    # The Cisco 3500XL is known to report incorrect duplex values.
    # Obsolete device, doesn't make sense supporting it.
    elif 'c2900PortLinkbeatStatus' in metadata:
        status_link = metadata['c2900PortLinkbeatStatus']
        status_duplex = metadata['c2900PortDuplexStatus']

        if status_link == 3:
            # If no link beats (Not AutoNegotiate)
            if status_duplex == 1:
                duplex = 2
            elif status_duplex == 2:
                duplex = 1
        else:
            # If link beats (AutoNegotiate)
            if status_duplex == 1:
                duplex = 4
            elif status_duplex == 2:
                duplex = 3

    # Return
    return duplex


def _trunk(metadata, ifindex):
    """Return trunk for specific ifIndex.

    Args:
        metadata: Data dict related to the device
        ifindex: ifindex in question

    Returns:
        trunk: True if port is in trunking mode

    """
    # Initialize key variables
    trunk = False

    # Determine if trunk for Cisco devices
    if 'vlanTrunkPortDynamicStatus' in metadata['layer1'][ifindex]:
        if metadata['layer1'][ifindex][
                'vlanTrunkPortDynamicStatus'] == 1:
            trunk = True

    # Determine if trunk for Juniper devices
    if 'jnxExVlanPortAccessMode' in metadata['layer1'][ifindex]:
        if metadata['layer1'][ifindex][
                'jnxExVlanPortAccessMode'] == 2:
            trunk = True

    # Return
    return trunk
