from enum import Enum, auto


class MessageResponseType(Enum):
    OK_SEND = auto()
    ERROR_SEND = auto()
    OK_SUBSCRIBE = auto()
    ERROR_SUBSCRIBE = auto()
    OK_UNSUBSCRIBE = auto()
    NEW_MESSAGE = auto()
    ERROR_UNSUBSCRIBE = auto()
    OK_USER = auto()
    ERROR_USER = auto()
