import argparse

TCP_SERVER_PORT = 65535 #last port available


def broker_initialize_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--socket_port",
                        help="Port number that will be assigned to broker's server socket",
                        required=False,
                        type=int,
                        default=TCP_SERVER_PORT)
    return parser.parse_args()
