import argparse

FLASK_PORT = 10000
TCP_SERVER_PORT = 10001


def initialize_parser():
    """Utility method that initializes argparse and return the args
        @rtype: Namespace object
        @returns: object built up from attributes parsed out of the command line
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--socket_port",
                        help="Port number that will be assigned to supervisor's socket",
                        required=False,
                        type=int,
                        default=TCP_SERVER_PORT)
    parser.add_argument("-fp", "--flask_port",
                        help="Port number that will be assigned to flask's server",
                        type=int,
                        required=False,
                        default=FLASK_PORT)
    return parser.parse_args()
