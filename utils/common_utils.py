import json

from netifaces import interfaces, ifaddresses, AF_INET
import re
from enums.Command import Command

command_regex = re.compile('^\[([A-Z]+)\]')
UPPER_AVAILABLE_PORT = 65535
LOWER_AVAILABLE_PORT = 49152


def get_host_address():
    for ifaceName in interfaces():
        addresses = ' '.join([i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr': ''}])])
        if addresses != '' and addresses != '0.0.0.0' and addresses != '127.0.0.1':
            return addresses
    return '127.0.0.1'


def get_command_and_value(message):
    """
    Get the command and the value from a tcp message
    :param message: message received from tcp value
    :return:
    """
    message = message.decode('UTF-8')
    if command_regex.match(message):
        message = message[1:]  # removing [
        split_message = message.split(']')
        command = Command[split_message[0]]
        value = split_message[1].strip()
        if command:
            value_casted = command.validate_and_return_casted_value(value)
            if value_casted:
                return command, value_casted
    raise ValueError("Not valid message.", 403)


def build_command(command, value):
    return f'[{command.name}] {value}'.encode('UTF-8')


def get_node_id(node_ip, node_port):
    return f'{node_ip}:{node_port}'
