from enum import Enum


class Status(str, Enum):
    PENDING = 'PENDING',
    CONFIRMED = 'CONFIRMED'
