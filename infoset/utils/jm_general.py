#!/usr/bin/env python3
"""Nagios check general library."""

import sys
import os
import datetime
import time
import shutil
import json
import yaml

# Infoset imports
from infoset.utils import jm_configuration


def log2die_safe(code, message):
    """Log message to STDOUT only and die.

    Args:
        code: Message code
        message: Message text

    Returns:
        None

    """
    # Initialize key variables
    output = _message(code, message, True)
    print(output)
    sys.exit(2)


def log2quiet(code, message):
    """Log message to file only, but don't die.

    Args:
        code: Message code
        message: Message text

    Returns:
        None

    """
    # Log to screen and file
    _logit(code, message, error=False, verbose=False)


def log2see(code, message):
    """Log message to file and STDOUT, but don't die.

    Args:
        code: Message code
        message: Message text

    Returns:
        None

    """
    # Log to screen and file
    _logit(code, message, error=False)


def log2die(code, message):
    """Log to STDOUT and file, then die.

    Args:
        code: Error number
        message: Descriptive error string

    Returns:
        None
    """
    _logit(code, message, error=True)


def _logit(code, message, error=True, verbose=True):
    """Log to STDOUT and File.

    Args:
        code: Error number
        message: Descriptive error string
        error: Is this an error or not?
        verbose: Quiet or not

    Returns:
        None

    """
    # Initialize key variables
    output = _message(code, message, error)

    # Log the message
    if error is True:
        print(output)
        _update_logfile(message)
        sys.exit(3)
    else:
        if verbose is True:
            print(output)
        _update_logfile(message)


def _update_logfile(message):
    """Write message to logfile.

    Args:
        message: Message to write

    Returns:
        None

    """
    # Get log filename
    config = jm_configuration.ConfigCommon(os.environ['INFOSET_CONFIGDIR'])
    filename = config.log_file()

    # Write to file
    with open(filename, 'a') as f_handle:
        f_handle.write(
            ('%s\n') % (message)
        )


def check_environment():
    """Check environmental variables. Die if incorrect.

    Args:
        None

    Returns:
        None

    """
    # Get environment
    if 'INFOSET_CONFIGDIR' not in os.environ:
        log_message = (
            'Environment variables $INFOSET_CONFIGDIR needs '
            'to be set to the infoset configuration directory.')
        log2die_safe(1041, log_message)

    # Get configuration directory
    config_directory = os.environ['INFOSET_CONFIGDIR']
    if (os.path.exists(config_directory) is False) or (
            os.path.isdir(config_directory) is False):
        log_message = (
            'Environment variables $INFOSET_CONFIGDIR set to '
            'directory %s that does not exist'
            '') % (config_directory)
        log2die_safe(1042, log_message)


def dict2yaml(data_dict):
    """Convert a dict to a YAML string.

    Args:
        data_dict: Data dict to convert

    Returns:
        yaml_string: YAML output
    """
    # Process data
    json_string = json.dumps(data_dict)
    yaml_string = yaml.dump(yaml.load(json_string), default_flow_style=False)

    # Return
    return yaml_string


def move_files(source_dir, target_dir):
    """Delete files in a directory.

    Args:
        source_dir: Directory where files are currently
        target_dir: Directory where files need to be

    Returns:
        Nothing

    """
    # Make sure source directory exists
    if os.path.exists(source_dir) is False:
        log_message = ('Directory %s does not exist.') % (
            source_dir)
        log2die(1011, log_message)

    # Make sure target directory exists
    if os.path.exists(target_dir) is False:
        log_message = ('Directory %s does not exist.') % (
            target_dir)
        log2die(1012, log_message)

    source_files = os.listdir(source_dir)
    for filename in source_files:
        full_path = ('%s/%s') % (source_dir, filename)
        shutil.move(full_path, target_dir)


def delete_files(target_dir):
    """Delete files in a directory.

    Args:
        target_dir: Directory in which files must be deleted

    Returns:
        Nothing

    """
    # Make sure target directory exists
    if os.path.exists(target_dir) is False:
        log_message = ('Directory %s does not exist.') % (
            target_dir)
        log2die(1013, log_message)

    # Delete all files in the tmp folder
    for the_file in os.listdir(target_dir):
        file_path = os.path.join(target_dir, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as exception_error:
            log_message = ('Error: deleting files in %s. Error: %s') % (
                target_dir, exception_error)
            log2die(1014, log_message)
        except:
            log_message = ('Unexpected error')
            log2die(1015, log_message)


def cleanstring(data):
    """Remove multiple whitespaces and linefeeds from string.

    Args:
        data: String to process

    Returns:
        result: Stipped data

    """
    # Initialize key variables
    nolinefeeds = data.replace('\n', ' ').replace('\r', '').strip()
    words = nolinefeeds.split()
    result = ' '.join(words)

    # Return
    return result


def _message(code, message, error=True):
    """Create a formatted message string.

    Args:
        code: Message code
        message: Message text
        error: If True, create a different message string

    Returns:
        output: Message result

    """
    # Initialize key variables
    time_object = datetime.datetime.fromtimestamp(time.time())
    timestring = time_object.strftime('%Y-%m-%d %H:%M:%S,%f')

    # Format string for error message, print and die
    if error is True:
        prefix = 'ERROR'
    else:
        prefix = 'STATUS'
    output = ('%s - %s - [%s] %s') % (timestring, prefix, code, message)

    # Return
    return output


def read_yaml_files(directories):
    """Read the contents of all yaml files in a directory.

    Args:
        directories: List of directory names with configuration files

    Returns:
        config_dict: Dict of yaml read

    """
    # Initialize key variables
    yaml_found = False
    yaml_from_file = ''
    all_yaml_read = ''

    # Check each directory in sequence
    for config_directory in directories:
        # Check if config_directory exists
        if os.path.isdir(config_directory) is False:
            log_message = (
                'Configuration directory "%s" '
                'doesn\'t exist!' % config_directory)
            log2die(1009, log_message)

        # Cycle through list of files in directory
        for filename in os.listdir(config_directory):
            # Examine all the '.yaml' files in directory
            if filename.endswith('.yaml'):
                # YAML files found
                yaml_found = True

                # Read file and add to string
                file_path = ('%s/%s') % (config_directory, filename)
                with open(file_path, 'r') as file_handle:
                    yaml_from_file = file_handle.read()

                # Append yaml from file to all yaml previously read
                all_yaml_read = ('%s\n%s') % (all_yaml_read, yaml_from_file)

        # Verify YAML files found in directory
        if yaml_found is False:
            log_message = (
                'No files found in directory "%s" with ".yaml" '
                'extension.') % (config_directory)
            log2die(1010, log_message)

    # Return
    config_dict = yaml.load(all_yaml_read)
    return config_dict
