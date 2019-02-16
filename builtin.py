from ast import Package, Primitive

ROOT_PACKAGE = Package('')
PLAY_PACKAGE = Package('play', ROOT_PACKAGE)
ROOT_PACKAGE.children['play'] = PLAY_PACKAGE

BOOLEAN_TYPE = Primitive("boolean")
BYTE_TYPE = Primitive("byte")
SHORT_TYPE = Primitive("short")
INT_TYPE = Primitive("int")
LONG_TYPE = Primitive("long")
FLOAT_TYPE = Primitive("float")
DOUBLE_TYPE = Primitive("double")
NULL_TYPE = Primitive('null')

BOX_CASTS = {
    'boolean': 'play.Boolean',
    'byte': 'play.Byte',
    'short': 'play.Short',
    'int': 'play.Int',
    'long': 'play.Long',
    'float': 'play.Float',
    'double': 'play.Double',
    'play.Boolean': 'boolean',
    'play.Byte': 'byte',
    'play.Short': 'short',
    'play.Int': 'int',
    'play.Long': 'long',
    'play.Float': 'float',
    'play.Double': 'double',
}

UPPER_CASTS = {
    'byte': {'short', 'int', 'long'},
    'short': {'int', 'long'},
    'int': {'long'},
    'float': {'double'},
}

# OBJECT_CLASS = Class("Object", PLAY_PACKAGE)
# OBJECT_CLASS.put(Method('equals', OBJECT_CLASS, parameters=[Parameter('other', ObjectType(OBJECT_CLASS))], return_type=BOOLEAN_TYPE))
# OBJECT_CLASS.inherited_members = OBJECT_CLASS.members

# STRING_CLASS = Class("String", PLAY_PACKAGE)

# LIST_CLASS = Class("List", PLAY_PACKAGE)
# BOOLEAN_LIST_CLASS = Class("BooleanList", PLAY_PACKAGE)
# BYTE_LIST_CLASS = Class("ByteList", PLAY_PACKAGE)
# SHORT_LIST_CLASS = Class("ShortList", PLAY_PACKAGE)
# INT_LIST_CLASS = Class("IntList", PLAY_PACKAGE)
# LONG_LIST_CLASS = Class("LongList", PLAY_PACKAGE)
# FLOAT_LIST_CLASS = Class("FloatList", PLAY_PACKAGE)
# DOUBLE_LIST_CLASS = Class("DoubleList", PLAY_PACKAGE)
# STRING_LIST_CLASS = Class("StringList", PLAY_PACKAGE)

# ITERABLE_CLASS = Class("Iterable", PLAY_PACKAGE, is_interface=True)
# BOOLEAN_ITERABLE_CLASS = Class("BooleanIterable", PLAY_PACKAGE, is_interface=True)
# BYTE_ITERABLE_CLASS = Class("ByteIterable", PLAY_PACKAGE, is_interface=True)
# SHORT_ITERABLE_CLASS = Class("ShortIterable", PLAY_PACKAGE, is_interface=True)
# INT_ITERABLE_CLASS = Class("IntIterable", PLAY_PACKAGE, is_interface=True)
# LONG_ITERABLE_CLASS = Class("LongIterable", PLAY_PACKAGE, is_interface=True)
# FLOAT_ITERABLE_CLASS = Class("FloatIterable", PLAY_PACKAGE, is_interface=True)
# DOUBLE_ITERABLE_CLASS = Class("DoubleIterable", PLAY_PACKAGE, is_interface=True)
# STRING_ITERABLE_CLASS = Class("StringIterable", PLAY_PACKAGE, is_interface=True)

# BOOLEAN_LIST_CLASS.interfaces = [BOOLEAN_ITERABLE_CLASS]
# BYTE_LIST_CLASS.interfaces = [BYTE_ITERABLE_CLASS]
# SHORT_LIST_CLASS.interfaces = [SHORT_ITERABLE_CLASS]
# INT_LIST_CLASS.interfaces = [INT_ITERABLE_CLASS]
# LONG_LIST_CLASS.interfaces = [LONG_ITERABLE_CLASS]
# FLOAT_LIST_CLASS.interfaces = [FLOAT_ITERABLE_CLASS]
# DOUBLE_LIST_CLASS.interfaces = [DOUBLE_ITERABLE_CLASS]
# STRING_LIST_CLASS.interfaces = [STRING_ITERABLE_CLASS]

# STD_CLASS = Class("Std", PLAY_PACKAGE)
# STD_CLASS.put(Method('print', STD_CLASS, is_static=True, parameters=[Parameter('str', ObjectType(STRING_CLASS))]))
# STD_CLASS.inherited_members = STD_CLASS.members


# @singleton
# class Builtin(object):
#     def __init__(self):
#         self.classes: Dict[str, Class] = {
#             "Object": Class("Object", PLAY_PACKAGE),
#
#             "Boolean": BOOLEAN_CLASS,
#             "Byte": BYTE_CLASS,
#             "Short": SHORT_CLASS,
#             "Int": INT_CLASS,
#             "Long": LONG_CLASS,
#             "Float": FLOAT_CLASS,
#             "Double": DOUBLE_CLASS,
#             "String": STRING_CLASS,
#
#             "List": LIST_CLASS,
#             "BooleanList": BOOLEAN_LIST_CLASS,
#             "ByteList": BYTE_LIST_CLASS,
#             "ShortList": SHORT_LIST_CLASS,
#             "IntList": INT_LIST_CLASS,
#             "LongList": LONG_LIST_CLASS,
#             "FloatList": FLOAT_LIST_CLASS,
#             "DoubleList": DOUBLE_LIST_CLASS,
#             "StringList": STRING_LIST_CLASS,
#
#             "Iterable": ITERABLE_CLASS,
#             "BooleanIterable": BOOLEAN_ITERABLE_CLASS,
#             "ByteIterable": BYTE_ITERABLE_CLASS,
#             "ShortIterable": SHORT_ITERABLE_CLASS,
#             "IntIterable": INT_ITERABLE_CLASS,
#             "LongIterable": LONG_ITERABLE_CLASS,
#             "FloatIterable": FLOAT_ITERABLE_CLASS,
#             "DoubleIterable": DOUBLE_ITERABLE_CLASS,
#             "StringIterable": STRING_ITERABLE_CLASS,
#
#             "Std": STD_CLASS,
#         }
INTEGER_NUMBERS = [BYTE_TYPE, SHORT_TYPE, INT_TYPE, LONG_TYPE]
REAL_NUMBERS = [FLOAT_TYPE, DOUBLE_TYPE]
NUMBERS = INTEGER_NUMBERS + REAL_NUMBERS
PRIMITIVES = NUMBERS + [BOOLEAN_TYPE]
