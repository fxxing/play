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
INTEGER_NUMBERS = [BYTE_TYPE, SHORT_TYPE, INT_TYPE, LONG_TYPE]
REAL_NUMBERS = [FLOAT_TYPE, DOUBLE_TYPE]
NUMBERS = INTEGER_NUMBERS + REAL_NUMBERS
PRIMITIVES = NUMBERS + [BOOLEAN_TYPE]
