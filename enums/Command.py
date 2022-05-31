import json
from enum import Enum, auto
import re


class Command(Enum):
    PORT = auto()
    RESULT = auto()
    SEND = auto()
    SUBSCRIBE = auto()
    UNSUBSCRIBE = auto()
    USER = auto()

    def validate_and_return_casted_value(self, value_to_cast):
        try:
            if self == Command.PORT:
                if re.compile("([1-9])([0-9]{3,})").match(value_to_cast):
                    return int(value_to_cast)
            elif self == Command.RESULT:
                if re.compile("[A-Z]+").match(value_to_cast):
                    return value_to_cast
            else:
                return json.loads(value_to_cast)
        except Exception as e:
            print(e)
        return None
