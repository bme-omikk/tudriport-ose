''' Enum3 kezelő modul: yes/no/not given reprezentálására készült adatszerkezet
'''

#yes/no/not given
ENUM3_YES = 'yes'
ENUM3_NO = 'no'
ENUM3_NA = 'not given'

def to_enum3(d, key, true_value):
    """ A d dictionary key kulcsa alapján készít enum3 értéket.

    Ha a kulcs nem szerepel a dictionary-ben, akkor not given.
    Ha a kulcs szerepel a dictionary-ben, és az értéke a true_value, akkor yes, egyébként no.
    """
    if key in d:
        if d[key] == true_value:
            return ENUM3_YES
        else:
            return ENUM3_NO
    else:
        return ENUM3_NA

def bool_to_enum3(b):
    if b:
        return ENUM3_YES
    else:
        return ENUM3_NO
