"""Generic classes for creating hidden files and directories."""

import os
import time

# Infoset imports
from infoset.utils import log
from infoset.utils import jm_general


class Directory:
    """A class for creating the names of hidden directories."""

    def __init__(self):
        """Method for intializing the class.

        Args:
            None

        Returns:
            None

        """
        # Initialize key variables
        self.root = ('%s/.infoset') % (jm_general.root_directory())

    def uid(self):
        """Method for defining the hidden uid directory.

        Args:
            None

        Returns:
            value: uid directory

        """
        # Return
        value = ('%s/uid') % self.root
        return value

    def snmp_cache(self):
        """Method for defining the hidden snmp_cache directory.

        Args:
            None

        Returns:
            value: snmp_cache directory

        """
        # Return
        value = ('%s/snmp_cache') % self.root
        return value

    def pid(self):
        """Method for defining the hidden pid directory.

        Args:
            None

        Returns:
            value: pid directory

        """
        # Return
        value = ('%s/pid') % self.root
        return value

    def lock(self):
        """Method for defining the hidden lock directory.

        Args:
            None

        Returns:
            value: lock directory

        """
        # Return
        value = ('%s/lock') % self.root
        return value


class File:
    """A class for creating the names of hidden files."""

    def __init__(self):
        """Method for intializing the class.

        Args:
            None

        Returns:
            None

        """
        # Initialize key variables
        self.directory = Directory()

    def uid(self, prefix):
        """Method for defining the hidden uid directory.

        Args:
            prefix: Prefix of file

        Returns:
            value: uid directory

        """
        # Return
        _mkdir(self.directory.uid())
        value = ('%s/%s.uid') % (self.directory.uid(), prefix)
        return value

    def snmp_cache(self, prefix):
        """Method for defining the hidden snmp_cache directory.

        Args:
            prefix: Prefix of file

        Returns:
            value: snmp_cache directory

        """
        # Return
        _mkdir(self.directory.snmp_cache())
        value = ('%s/%s.yaml') % (self.directory.snmp_cache(), prefix)
        return value

    def pid(self, prefix):
        """Method for defining the hidden pid directory.

        Args:
            prefix: Prefix of file

        Returns:
            value: pid directory

        """
        # Return
        _mkdir(self.directory.pid())
        value = ('%s/%s.pid') % (self.directory.pid(), prefix)
        return value

    def lock(self, prefix):
        """Method for defining the hidden lock directory.

        Args:
            prefix: Prefix of file

        Returns:
            value: lock directory

        """
        # Return
        _mkdir(self.directory.lock())
        value = ('%s/%s.lock') % (self.directory.lock(), prefix)
        return value


class Touch:
    """A class for updating modifed times for hidden files."""

    def __init__(self):
        """Method for intializing the class.

        Args:
            None

        Returns:
            None

        """
        # Initialize key variables
        self.filez = File()

    def pid(self, prefix):
        """Method for updating the hidden pid file.

        Args:
            prefix: Prefix of file

        Returns:
            value: uid directory

        """
        # Return
        timestamp = int(time.time())
        filename = self.filez.pid(prefix)
        os.utime(filename, (timestamp, timestamp))


def _mkdir(directory):
    """Create a directory if it doesn't already exist.

    Args:
        directory: Directory name

    Returns:
        None

    """
    # Do work
    if os.path.exists(directory) is False:
        os.makedirs(directory)
    else:
        if os.path.isfile(directory) is True:
            log_message = (
                '%s is not a directory.'
                '') % (directory)
            log.log2die(1043, log_message)
