from enum import Enum


class Command(str, Enum):
    PORT = "([1-9]{1})([0-9]{3,})"

    def cast_value(self, value_to_cast):
        if self.name == Command.PORT.name:
            return int(value_to_cast)
