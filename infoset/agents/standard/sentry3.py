#!/usr/bin/env python3
"""infoset Sentry3 (Servertech intelligent CDU power strip) agent.

Description:

    This script:
        1) Retrieves a variety of system information
        2) Posts the data using HTTP to a server listed
           in the configuration file

"""
# Standard libraries
from threading import Timer
import logging
import argparse
from collections import defaultdict

# infoset libraries
from infoset.agents import agent
from infoset.utils import jm_configuration
from infoset.utils import jm_general
from infoset.snmp import snmp_manager
from infoset.snmp import mib_sentry3

logging.getLogger('requests').setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG)


class PollingAgent(object):
    """Infoset agent that gathers data.

    Args:
        None

    Returns:
        None

    Functions:
        __init__:
        populate:
        post:
    """

    def __init__(self, config_dir):
        """Method initializing the class.

        Args:
            config_dir: Configuration directory

        Returns:
            None

        """
        # Initialize key variables
        agent_name = 'sentry3'

        # Get configuration
        self.config = jm_configuration.ConfigAgent(config_dir, agent_name)

        # Get snmp configuration information from infoset
        self.snmp_config = jm_configuration.ConfigSNMP(config_dir)

    def query(self):
        """Query all remote hosts for data.

        Args:
            None

        Returns:
            None

        """
        # Initialize key variables
        log_file = self.config.log_file()

        # Check each hostname
        hostnames = self.config.agent_snmp_hostnames()
        for hostname in hostnames:
            # Get valid SNMP credentials
            validate = snmp_manager.Validate(
                hostname, self.snmp_config.snmp_auth())
            snmp_params = validate.credentials()

            # Log message
            if snmp_params is None:
                log_message = (
                    'No valid SNMP configuration found '
                    'for host "%s" ') % (hostname)
                jm_general.log(1006, log_message, log_file, error=False)
                continue

            # Create Query make sure MIB is supported
            snmp_object = snmp_manager.Interact(snmp_params)
            snmp_query = mib_sentry3.init_query(snmp_object)
            if snmp_query.supported() is False:
                log_message = (
                    'The Sentry3 MIB is not supported by host  "%s"'
                    '') % (hostname)
                jm_general.log(1001, log_message, log_file, error=False)
                continue

            # Get the UID for the agent after all preliminary checks are OK
            uid_env = agent.get_uid(hostname)

            # Post data to the remote server
            self.upload(uid_env, hostname, snmp_query)

        # Do the daemon thing
        Timer(300, self.query()).start()

    def upload(self, uid, hostname, query):
        """Post system data to the central server.

        Args:
            uid: Unique ID for Agent
            hostname: Hostname
            query: SNMP credentials object

        Returns:
            None

        """
        # Initialize key variables
        agent_obj = agent.Agent(uid, self.config, hostname)
        state = {}
        data = defaultdict(lambda: defaultdict(dict))
        labels = ['infeedPower', 'infeedLoadValue']
        prefix = 'Sentry3'

        # Get results from querying Servertech device
        state['infeedPower'] = _normalize_keys(query.infeedpower())
        state['infeedLoadValue'] = _normalize_keys(
            query.infeedloadvalue())
        state['infeedID'] = _normalize_keys(query.infeedid())

        # Create dictionary for eventual posting
        for label in labels:
            for key, value in state[label].items():
                source = state['infeedID'][key]
                data[label][source] = value

        # Populate agent
        agent_obj.populate_dict(prefix, data)

        # Post data
        success = agent_obj.post()

        # Purge cache if success is True
        if success is True:
            agent_obj.purge()


def _normalize_keys(data, nodes=2):
    """Normalize SNMP results.

    Args:
        data: Dict of results
        nodes: Last number of nodes in OID to use as a key

    Returns:
        result: Dict with new key

    """
    # Initialize key variables
    intermediate = {}
    result = {}
    count = 0

    # Iterate
    for key, value in data.items():
        nodes = key.split('.')
        new_key = ('%s.%s') % (nodes[-2], nodes[-1])
        intermediate[new_key] = value

    # Do again but convert to numeric keys
    for _, value in sorted(intermediate.items()):
        result[count] = value
        count += 1

    # Return
    return result


def process_cli(additional_help=None):
    """Return all the CLI options.

    Args:
        None

    Returns:
        args: Namespace() containing all of our CLI arguments as objects
            - filename: Path to the configuration file

    """
    # Header for the help menu of the application
    parser = argparse.ArgumentParser(
        description=additional_help,
        formatter_class=argparse.RawTextHelpFormatter)

    # CLI argument for the auth directory
    parser.add_argument(
        '--config_dir',
        dest='config_dir',
        required=True,
        default=None,
        type=str,
        help='Configuration directory to use.'
    )

    # Return the CLI arguments
    args = parser.parse_args()

    # Return our parsed CLI arguments
    return args


def main():
    """Start the infoset agent.

    Args:
        None

    Returns:
        None

    """
    # Get configuration
    args = process_cli()

    # Instantiate and poll
    poller = PollingAgent(args.config_dir)
    poller.query()

if __name__ == "__main__":
    main()
