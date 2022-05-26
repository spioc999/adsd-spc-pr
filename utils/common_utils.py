from netifaces import interfaces, ifaddresses, AF_INET
import re
from enums.Command import Command

command_regex = re.compile('^\[([A-Z]+)\]')


def get_host_address():
    for ifaceName in interfaces():
        addresses = ' '.join([i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr': ''}])])
        if addresses != '' and addresses != '0.0.0.0' and addresses != '127.0.0.1':
            return addresses
    return '127.0.0.1'


def get_command_and_value(message):
    """

    :param message: get the command and the value from a tcp message
    :return:
    """
    if command_regex.match(message):
        message = message[1:]  # removing [
        split_message = message.split(']')
        command = Command[split_message[0]]
        value = split_message[1].strip()
        if re.compile(command).match(value):
            return command, command.cast_value(value)
    raise ValueError("Command doesn't match the regex!")
