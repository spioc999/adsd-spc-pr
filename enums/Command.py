from enum import Enum


class Command(str, Enum):
    PORT = "([1-9]{1})([0-9]{3,})"
    RESULT = "[A-Z]+"

    def cast_value(self, value_to_cast):
        if self.name == Command.PORT.name:
            return int(value_to_cast)
        else:  # in case of str value
            return value_to_cast
