#!/usr/bin/env python3

"""Demonstration Script that extracts agent data from cache directory files.

This could be a modified to be a daemon

"""

# Standard libraries
import os
import time
import shutil
import json
import hashlib
from collections import defaultdict
import queue as Queue
import threading
import re

# Infoset libraries
from infoset.db import db
from infoset.db import db_agent as agent
from infoset.utils import log
from infoset.utils import jm_general

# Define a key global variable
THREAD_QUEUE = Queue.Queue()


class Drain(object):
    """Infoset class that ingests agent data.

    Args:
        None

    Returns:
        None

    Methods:
        __init__:
        populate:
        post:
    """

    def __init__(self, filename):
        """Method initializing the class.

        Args:
            filename: Cache filename

        Returns:
            None

        """
        # Initialize key variables
        self.filename = filename
        self.data = defaultdict(lambda: defaultdict(dict))
        self.metadata = []
        self.validated = False
        read_failure = False
        self.agent_meta = {}
        data_types = ['chartable', 'other']
        agent_meta_keys = ['timestamp', 'uid', 'agent', 'hostname']
        information = {}

        # Ingest data
        try:
            with open(filename, 'r') as f_handle:
                information = json.load(f_handle)
        except:
            read_failure = True

        # Validate data read from file.
        # Provide information for self.valid() method.
        # Stop further processing if invalid
        if read_failure is False:
            self.validated = _validated(information, filename)
        else:
            self.validated = False
        if self.validated is False:
            log_message = (
                'Cache ingest file %s is invalid.') % (filename)
            log.log2warn(1051, log_message)
            return

        # Get universal parameters from file
        for key in agent_meta_keys:
            self.agent_meta[key] = information[key]
        timestamp = int(information['timestamp'])
        uid = information['uid']

        # Process chartable data
        for data_type in data_types:
            # Skip if data type isn't in the data
            if data_type not in information:
                continue

            # Process the data type
            for label, group in sorted(information[data_type].items()):
                # Get universal parameters for group
                base_type = _base_type(group['base_type'])
                description = group['description']

                # Initialize base type
                if base_type not in self.data[data_type]:
                    self.data[data_type][base_type] = []

                # Process data
                for datapoint in group['data']:
                    index = datapoint[0]
                    value = datapoint[1]
                    source = datapoint[2]
                    did = _did(uid, label, index)

                    # Update data
                    self.data[data_type][base_type].append(
                        (uid, did, value, timestamp)
                    )

                    # Update sources
                    self.metadata.append(
                        (uid, did, label, source, description, base_type)
                    )

    def valid(self):
        """Determine whether data is valid.

        Args:
            None

        Returns:
            isvalid: Valid if true

        """
        # Initialize key variables
        isvalid = self.validated

        # Return
        return isvalid

    def uid(self):
        """Return uid.

        Args:
            None

        Returns:
            data: Agent UID

        """
        # Initialize key variables
        data = self.agent_meta['uid']

        # Return
        return data

    def timestamp(self):
        """Return timestamp.

        Args:
            None

        Returns:
            data: Agent timestamp

        """
        # Initialize key variables
        data = int(self.agent_meta['timestamp'])

        # Return
        return data

    def agent(self):
        """Return agent.

        Args:
            None

        Returns:
            data: Agent agent_name

        """
        # Initialize key variables
        data = self.agent_meta['agent']

        # Return
        return data

    def hostname(self):
        """Return hostname.

        Args:
            None

        Returns:
            data: Agent hostname

        """
        # Initialize key variables
        data = self.agent_meta['hostname']

        # Return
        return data

    def counter32(self):
        """Return counter32 chartable data from file.

        Args:
            None

        Returns:
            data: List of tuples (uid, did, value, timestamp)
                uid = UID of device providing data
                did = Datapoint ID
                value = Value of datapoint
                timestamp = Timestamp when data was collected by the agent

        """
        # Initialize key variables
        data = []

        # Get data
        if 'chartable' in self.data:
            if 32 in self.data['chartable']:
                data = self.data['chartable'][32]

        # Return
        return data

    def counter64(self):
        """Return counter64 chartable data from file.

        Args:
            None

        Returns:
            data: List of tuples (uid, did, value, timestamp)
                uid = UID of device providing data
                did = Datapoint ID
                value = Value of datapoint
                timestamp = Timestamp when data was collected by the agent

        """
        # Initialize key variables
        data = []

        # Get data
        if 'chartable' in self.data:
            if 64 in self.data['chartable']:
                data = self.data['chartable'][64]

        # Return
        return data

    def floating(self):
        """Return floating chartable data from file.

        Args:
            None

        Returns:
            data: List of tuples (uid, did, value, timestamp)
                uid = UID of device providing data
                did = Datapoint ID
                value = Value of datapoint
                timestamp = Timestamp when data was collected by the agent

        """
        # Initialize key variables
        data = []

        # Get data
        if 'chartable' in self.data:
            if 1 in self.data['chartable']:
                data = self.data['chartable'][1]

        # Return
        return data

    def chartable(self):
        """Return all chartable data from file.

        Args:
            None

        Returns:
            data: List of tuples (uid, did, value, timestamp)
                uid = UID of device providing data
                did = Datapoint ID
                value = Value of datapoint
                timestamp = Timestamp when data was collected by the agent

        """
        # Initialize key variables
        data = []

        # Initialize key variables
        data.extend(self.floating())
        data.extend(self.counter32())
        data.extend(self.counter64())

        # Return
        return data

    def other(self):
        """Return other non-chartable data from file.

        Args:
            None

        Returns:
            data: List of tuples (uid, did, value, timestamp)
                uid = UID of device providing data
                did = Datapoint ID
                value = Value of datapoint
                timestamp = Timestamp when data was collected by the agent

        """
        # Initialize key variables
        data = []

        # Return (Ignore whether floating or counter)
        if 'other' in self.data:
            for _, value in self.data['other'].items():
                data.extend(value)
        return data

    def sources(self):
        """Return sources data from file.

        Args:
            None

        Returns:
            data: List of tuples (uid, did, label, source, description)
                uid = UID of device providing data
                did = Datapoint ID
                label = Label that the agent gave the category of datapoint
                source = Subsystem that provided the data in the datapoint
                description = Description of the label
                base_type = SNMP base type code (Counter32, Gauge etc.)

        """
        # Initialize key variables
        data = self.metadata

        # Return
        return data

    def purge(self):
        """Purge cache file that was read.

        Args:
            None

        Returns:
            success: "True" if successful

        """
        # Initialize key variables
        success = True

        try:
            os.remove(self.filename)
        except:
            success = False

        # Report success
        if success is True:
            log_message = (
                'Ingest cache file %s deleted') % (self.filename)
            log.log2quiet(1046, log_message)
        else:
            log_message = (
                'Failed to delete ingest cache file %s') % (self.filename)
            log.log2warn(1050, log_message)

        # Return
        return success


class FillDB(threading.Thread):
    """Threaded polling.

    Graciously modified from:
    http://www.ibm.com/developerworks/aix/library/au-threadingpython/

    """

    def __init__(self, queue):
        """Initialize the threads."""
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        """Update the database using threads."""
        while True:
            # Get the data_dict
            data_dict = self.queue.get()
            uid = data_dict['uid']
            metadata = data_dict['metadata']
            config = data_dict['config']
            agents = data_dict['agents']
            datapoints = data_dict['datapoints']

            # Sort metadata by timestamp
            metadata.sort()

            # Process file for each timestamp
            for (timestamp, filepath) in metadata:
                # Read in data
                ingest = Drain(filepath)

                # Make sure file is OK
                # Move it to a directory for further analysis
                # by administrators
                if ingest.valid() is False:
                    log_message = (
                        'Cache ingest file %s is invalid. Moving.'
                        '') % (filepath)
                    log.log2warn(1054, log_message)
                    shutil.move(
                        filepath, config.ingest_failures_directory())
                    continue

                # Double check that the UID and timestamp in the
                # filename matches that in the file.
                # Ignore invalid files as a safety measure.
                # Don't try to delete. They could be owned by some
                # one else and the daemon could crash
                if uid != ingest.uid():
                    continue
                if timestamp != ingest.timestamp():
                    continue
                if jm_general.validate_timestamp(
                        ingest.timestamp()) is False:
                    continue

                # Update agent table if not there
                if ingest.uid() not in agents:
                    _insert_agent(
                        ingest.uid(),
                        ingest.agent(),
                        ingest.hostname(),
                        config
                        )
                    # Append the new insertion to the list
                    agents.append(ingest.uid())

                # Update datapoint metadata if not there
                for item in ingest.sources():
                    did = item[1]
                    if did not in datapoints:
                        _insert_datapoint(item, config)
                        # Append the new insertion to the list
                        datapoints.append(did)

                # Update chartable data
                _update_measurements(ingest, config)

                # Purge source file
                ingest.purge()

            # All done!
            self.queue.task_done()


def _update_measurements(ingest, config):
    """Insert data into the database "iset_data" table.

    Args:
        ingest: Drain object
        config: Config object

    Returns:
        None

    """
    # Initialize key variables
    data = ingest.chartable()
    data_list = []
    timestamp_tracker = {}

    # Create map of DIDs to database row index values
    mapping = _datapoints_by_did(config)

    # Update data
    for item in data:
        # Process each datapoint item found
        (_, did, tuple_value, timestamp) = item
        idx_datapoint = int(mapping[did][0])
        idx_agent = int(mapping[did][1])
        last_timestamp = int(mapping[did][2])
        value = float(tuple_value)

        # Only update with data collected after
        # the most recent update. Don't do anything more
        if timestamp > last_timestamp:
            data_list.append(
                (idx_datapoint, idx_agent, value, timestamp)
            )
            continue

        # Update DID's last updated timestamp
        if idx_datapoint in timestamp_tracker:
            timestamp_tracker[idx_datapoint] = max(
                timestamp, timestamp_tracker[idx_datapoint])
        else:
            timestamp_tracker[idx_datapoint] = timestamp

    # Update if there is data
    if bool(data_list) is True:
        # Prepare SQL query to read a record from the database.
        sql_insert = (
            'REPLACE INTO iset_data '
            '(idx_datapoint, idx_agent, value, timestamp) VALUES '
            '(%s, %s, %s, %s)')

        # Do query and get results
        database = db.Database(config)
        database.modify(sql_insert, 1037, data_list=data_list)

        # Change the last updated timestamp
        for idx_datapoint, last_timestamp in timestamp_tracker.items():
            # Prepare SQL query to read a record from the database.
            sql_modify = (
                'UPDATE iset_datapoint SET last_timestamp=%s '
                'WHERE iset_datapoint.idx=%s'
                '') % (last_timestamp, idx_datapoint)
            database.modify(sql_modify, 1044)

        # Report success
        log_message = ('Successful cache drain for UID %s at timestamp %s') % (
            ingest.uid(), ingest.timestamp())
        log.log2quiet(1045, log_message)


def _insert_datapoint(metadata, config):
    """Insert new datapoint into database.

    Args:
        metadata: Tuple of datapoint metadata.
            (uid, did, label, source, description)
            uid: Agent UID
            did: Datapoint ID
            label: Datapoint label created by agent
            source: Source of the data (subsystem being tracked)
            description: Description provided by agent config file (unused)
            base_type = SNMP base type (Counter32, Counter64, Gauge etc.)
        config: Configuration object

    Returns:
        None

    """
    # Initialize key variables
    (uid, did, label, source, _, base_type) = metadata

    # Get agent index value
    agent_object = agent.Get(uid, config)
    idx_agent = agent_object.idx()

    # Prepare SQL query to read a record from the database.
    sql_query = (
        'INSERT INTO iset_datapoint '
        '(id, idx_agent, agent_label, agent_source, base_type ) VALUES '
        '("%s", %d, "%s", "%s", %d)'
        '') % (did, idx_agent, label, source, base_type)

    # Do query and get results
    database = db.Database(config)
    database.modify(sql_query, 1032)


def _insert_agent(uid, name, hostname, config):
    """Insert new agent into database.

    Args:
        uid: Agent uid
        name: Agent name
        Hostname: Hostname the agent gets data from
        config: Configuration object

    Returns:
        None

    """
    # Prepare SQL query to read a record from the database.
    sql_query = (
        'INSERT INTO iset_agent (id, name, hostname) '
        'VALUES ("%s", "%s", "%s")'
        '') % (uid, name, hostname)

    # Do query and get results
    database = db.Database(config)
    database.modify(sql_query, 1033)


def _datapoints(config):
    """Create list of enabled datapoints.

    Args:
        config: Configuration object

    Returns:
        data: List of active datapoints

    """
    # Initialize key variables
    data = []

    # Prepare SQL query to read a record from the database.
    sql_query = (
        'SELECT iset_datapoint.id '
        'FROM iset_datapoint WHERE (iset_datapoint.enabled=1)')

    # Do query and get results
    database = db.Database(config)
    query_results = database.query(sql_query, 1034)

    # Massage data
    for row in query_results:
        data.append(row[0])

    # Return
    return data


def _datapoints_by_did(config):
    """Create dict of enabled datapoints and their corresponding indices.

    Args:
        config: Configuration object

    Returns:
        data: Dict keyed by datapoint ID,
            with a tuple as its value (idx, idx_agent)
            idx: Datapoint index
            idx_agent: Agent index
            last_timestamp: The last time the timestamp was updated

    """
    # Initialize key variables
    data = {}

    # Prepare SQL query to read a record from the database.
    sql_query = (
        'SELECT iset_datapoint.id, iset_datapoint.idx, '
        'iset_datapoint.idx_agent, iset_datapoint.last_timestamp '
        'FROM iset_datapoint WHERE (iset_datapoint.enabled=1)')

    # Do query and get results
    database = db.Database(config)
    query_results = database.query(sql_query, 1035)

    # Massage data
    for row in query_results:
        did = row[0]
        idx = row[1]
        idx_agent = row[2]
        last_timestamp = row[3]
        data[did] = (idx, idx_agent, last_timestamp)

    # Return
    return data


def _agents(config):
    """Create list of active agent UIDs.

    Args:
        config: Configuration object

    Returns:
        data: List of active agents

    """
    # Initialize key variables
    data = []

    # Prepare SQL query to read a record from the database.
    sql_query = (
        'SELECT iset_agent.id '
        'FROM iset_agent WHERE (iset_agent.enabled=1)')

    # Do query and get results
    database = db.Database(config)
    query_results = database.query(sql_query, 1036)

    # Massage data
    for row in query_results:
        data.append(row[0])

    # Return
    return data


def _did(uid, label, index):
    """Create a unique DID from ingested data.

    Args:
        uid: UID of device that created the cache data file
        label: Label of the data
        index: Index of the data

    Returns:
        did: Datapoint ID

    """
    # Initialize key variables
    prehash = ('%s%s%s') % (uid, label, index)
    hasher = hashlib.sha256()
    hasher.update(bytes(prehash.encode()))
    did = hasher.hexdigest()

    # Return
    return did


def _base_type(data):
    """Create a base_type integer value from the string sent by agents.

    Args:
        data: base_type value as string

    Returns:
        base_type: Base type value as integer

    """
    # Initialize key variables
    if bool(data) is False:
        value = 'NULL'
    else:
        value = data

    # Assign base type code
    if value.lower() == 'floating':
        base_type = 1
    elif value.lower() == 'counter32':
        base_type = 32
    elif value.lower() == 'counter64':
        base_type = 64
    else:
        base_type = 0

    # Return
    return base_type


def _validated(information, filename):
    """Validate incoming agent json data.

    Args:
        information: Agent json data
        filename: Filename that provided the data

    Returns:
        valid: True if validated

    """
    # Initialize key variables
    valid = True
    agent_name = 'Unknown'
    data_types = ['chartable', 'other']
    agent_meta_keys = ['timestamp', 'uid', 'agent', 'hostname']

    # Get universal parameters from file
    for key in agent_meta_keys:
        if key not in information:
            valid = False

    # Get agent name for future reporting
    if valid is True:
        agent_name = information['agent']

    # Timestamp must be an integer
    try:
        int(information['timestamp'])
    except:
        valid = False

    # Process chartable data
    for data_type in data_types:
        # Skip if data type isn't in the data
        if data_type not in information:
            continue

        # Process the data type
        for category, group in sorted(information[data_type].items()):
            # Process keys
            for key in ['base_type', 'description', 'data']:
                if key not in group:
                    valid = False

            # Process data
            for datapoint in group['data']:
                if len(datapoint) != 3:
                    valid = False

                # Check to make sure value is numeric
                if category == 'chartable':
                    value = datapoint[1]
                    try:
                        float(value)
                    except:
                        valid = False

    # Error message
    if valid is False:
        log_message = (
            'Cache file %s for agent %s is invalid'
            '') % (filename, agent_name)
        log.log2warn(1021, log_message)

    # Return
    return valid


def process(config):
    """Method initializing the class.

    Args:
        config: Configuration object

    Returns:
        None

    """
    # Initialize key variables
    threads_in_pool = config.ingest_threads()
    uid_metadata = defaultdict(lambda: defaultdict(dict))
    cache_dir = config.ingest_cache_directory()

    # Filenames must start with a numeric timestamp and #
    # end with a hex string. This will be tested later
    regex = re.compile(r'^\d+_[0-9a-f]+.json')

    # Get a list of active agents and datapoints
    agents = _agents(config)
    datapoints = _datapoints(config)

    # Spawn a pool of threads, and pass them queue instance
    for _ in range(threads_in_pool):
        update_thread = FillDB(THREAD_QUEUE)
        update_thread.daemon = True
        update_thread.start()

    # Add files in cache directory to list
    all_filenames = [filename for filename in os.listdir(
        cache_dir) if os.path.isfile(
            os.path.join(cache_dir, filename))]

    ######################################################################
    # Create threads
    ######################################################################

    # Process only valid agent filenames
    for filename in all_filenames:
        # Add valid data to lists
        if bool(regex.match(filename)) is True:
            # Create a complete filepath
            filepath = os.path.join(cache_dir, filename)

            # Only read files that are 15 seconds or older
            # to prevent corruption caused by reading a file that could be
            # updating simultaneously
            if time.time() - os.path.getmtime(filepath) < 15:
                continue

            # Create a dict of UIDs, timestamps and filepaths
            (name, _) = filename.split('.')
            (tstamp, uid) = name.split('_')
            timestamp = int(tstamp)
            if uid in uid_metadata:
                uid_metadata[uid].append(
                    (timestamp, filepath))
            else:
                uid_metadata[uid] = [(timestamp, filepath)]

    # Read each cache file
    for uid in uid_metadata.keys():

        ####################################################################
        #
        # Define variables that will be required for the threading
        # We have to initialize the dict during every loop to prevent
        # data corruption
        #
        ####################################################################
        data_dict = {}
        data_dict['uid'] = uid
        data_dict['metadata'] = uid_metadata[uid]
        data_dict['config'] = config
        data_dict['agents'] = agents
        data_dict['datapoints'] = datapoints
        THREAD_QUEUE.put(data_dict)

    # Wait on the queue until everything has been processed
    THREAD_QUEUE.join()

    # PYTHON BUG. Join can occur while threads are still shutting down.
    # This can create spurious "Exception in thread (most likely raised
    # during interpreter shutdown)" errors.
    # The "time.sleep(1)" adds a delay to make sure things really terminate
    # properly. This seems to be an issue on virtual machines in Dev only
    time.sleep(1)
