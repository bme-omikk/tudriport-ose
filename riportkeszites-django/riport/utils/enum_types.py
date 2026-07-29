from enum import IntEnum

class IntEnumWithDescription(IntEnum):
    """Extends IntEnum (from python standard lib) with description"""
    # example to use:
    #FIRST_MEMBER = 0, 'this is first member'
    #SECOND_MEMBER = 5, 'a big step in value'
    #
    # based on https://stackoverflow.com/a/64040739
    def __new__(cls, intvalue, description):
        member = int.__new__(cls, intvalue)
        member._value_ = intvalue
        member.description = description
        return member

