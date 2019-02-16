grammar Play;

compilationUnit: importDeclaration* classDeclaration EOF;
qualifiedName: IDENTIFIER ('.' IDENTIFIER)*;
typeName
    : 'boolean'
    | 'byte'
    | 'short'
    | 'int'
    | 'long'
    | 'float'
    | 'double'
    | classType
    ;
literal
    : DECIMAL_LITERAL
    | HEX_LITERAL
    | OCT_LITERAL
    | BINARY_LITERAL
    | FLOAT_LITERAL
    | BYTE_LITERAL
    | STRING_LITERAL
    | BOOL_LITERAL
    | NULL_LITERAL
    ;
importDeclaration: 'import' qualifiedName;
classDeclaration: 'native'? ('class' | 'interface') IDENTIFIER (':' classTypeList)? '{' memberDeclaration* '}';
memberDeclaration: methodDeclaration| fieldDeclaration;
classTypeList: classType (',' classType)*;
classType: IDENTIFIER;
//methodDeclaration: ('static' | 'extern')? 'def' IDENTIFIER '(' parameters? ')' ('->' typeName)? ('throws' classTypeList)? block?;
methodDeclaration: 'native'? 'static'? 'def' IDENTIFIER '(' parameters? ')' ('->' typeName)? block?;
parameters: variable (',' variable)*;
variable: IDENTIFIER ':' typeName;
fieldDeclaration: variable ('=' expression)?;
// ==============================================================================================
// statement
// ==============================================================================================
block: '{' statement* '}';
statement
    : ifStatement
//    | forStatement
    | whileStatement
    | breakStatement
    | continueStatement
    | returnStatement
    | assignStatement
//    | tryStatement
//    | throwStatement
    | expression
    | block
    ;
ifStatement: 'if' expression block elifClause* elseClause?;
elifClause: 'elif' expression block;
elseClause: 'else' block;
//forStatement: 'for' IDENTIFIER 'in' expression block;
whileStatement: 'while' expression block;
returnStatement: 'return' expression?;
//throwStatement: 'throw' expression?;
breakStatement: 'break';
continueStatement: 'continue';
assignStatement: (IDENTIFIER (':' typeName)? | expression) '=' expression;
//tryStatement: 'try' block catchClause+ finallyClause?;
//catchClause: 'catch' '(' IDENTIFIER ':' catchTypes ')' block;
//catchTypes: IDENTIFIER ('|' IDENTIFIER)*;
//finallyClause: 'finally' block;
// ==============================================================================================
// expression
// ==============================================================================================
expression
    : expression bop='.' methodCall
    | expression bop='.' IDENTIFIER
    | logicalOrExpression
    ;
logicalOrExpression
    : logicalAndExpression
    | logicalOrExpression bop='||' logicalAndExpression
    ;
logicalAndExpression
    : inclusiveOrExpression
    | logicalAndExpression bop='&&' inclusiveOrExpression
    ;
inclusiveOrExpression
    : exclusiveOrExpression
    | inclusiveOrExpression bop='|' exclusiveOrExpression
    ;
exclusiveOrExpression
    :  andExpression
    |  exclusiveOrExpression bop='^' andExpression
    ;
andExpression
    : equalityExpression
    | andExpression bop='&' equalityExpression
    ;
equalityExpression
    : relationalExpression
    | equalityExpression bop='==' relationalExpression
    | equalityExpression bop='!=' relationalExpression
    ;
relationalExpression
    : shiftExpression
    | relationalExpression bop='<' shiftExpression
    | relationalExpression bop='>' shiftExpression
    | relationalExpression bop='<=' shiftExpression
    | relationalExpression bop='>=' shiftExpression
    ;
shiftExpression
    : additiveExpression
    | shiftExpression bop='<<' additiveExpression
    | shiftExpression bop='>>' additiveExpression
    | shiftExpression bop='>>>' additiveExpression
    ;
additiveExpression
    : multiplicativeExpression
    | additiveExpression bop='+' multiplicativeExpression
    | additiveExpression bop='-' multiplicativeExpression
    ;
multiplicativeExpression
    : castExpression
    | multiplicativeExpression bop='*' castExpression
    | multiplicativeExpression bop='/' castExpression
    | multiplicativeExpression bop='%' castExpression
    ;
castExpression
    : castExpression bop='as' typeName
    | unaryExpression
    ;
unaryExpression
    : uop=('+' | '-' | '~' | '!') castExpression
    | primaryExpression
    ;
primaryExpression
    : methodCall
    | classCreation
    | 'this'
    | 'super'
    | literal
    | IDENTIFIER
    | '(' expression ')'
    ;
classCreation: 'new' classType '(' expressionList? ')';
methodCall: (IDENTIFIER | 'this' | 'super') '(' expressionList? ')';
expressionList: expression (',' expression)*;

// ==============================================================================================
// tokens
// ==============================================================================================

// Keywords

BOOLEAN:            'boolean';
BYTE:               'byte';
SHORT:              'short';
INT:                'int';
LONG:               'long';
FLOAT:              'float';
DOUBLE:             'double';

IMPORT:             'import';
CLASS:              'class';
INTERFACE:          'interface';
DEF:                'def';
STATIC:             'static';
NATIVE:             'native';

THIS:               'this';
SUPER:              'super';

IF:                 'if';
ELSE:               'else';
ELIF:               'elif';
//FOR:                'for';
IN:                 'in';
WHILE:              'while';
BREAK:              'break';
CONTINUE:           'continue';
RETURN:             'return';
TRY:                'try';
CATCH:              'catch';
FINALLY:            'finally';
THROW:              'throw';
THROWS:             'throws';

AS:                 'as';
NEW:                'new';

// Literals

DECIMAL_LITERAL:    ('0' | [1-9] (Digits? | '_'+ Digits)) [lL]?;
HEX_LITERAL:        '0' [xX] [0-9a-fA-F] ([0-9a-fA-F_]* [0-9a-fA-F])? [lL]?;
OCT_LITERAL:        '0' '_'* [0-7] ([0-7_]* [0-7])? [lL]?;
BINARY_LITERAL:     '0' [bB] [01] ([01_]* [01])? [lL]?;

FLOAT_LITERAL:      (Digits '.' Digits? | '.' Digits) ExponentPart? [fFdD]?
             |       Digits (ExponentPart [fFdD]? | [fFdD])
             ;

BOOL_LITERAL:       'true' | 'false';

BYTE_LITERAL:       '\'' (~['\\\r\n] | EscapeSequence) '\'';

STRING_LITERAL:     '"' (~["\\\r\n] | EscapeSequence)* '"';

NULL_LITERAL:       'null';

// Separators

LPAREN:             '(';
RPAREN:             ')';
LBRACE:             '{';
RBRACE:             '}';
LBRACK:             '[';
RBRACK:             ']';
COMMA:              ',';
DOT:                '.';

COLONCOLON:         '::';
COLON:              ':';
ARROW:              '->';
AT:                 '@';

// Operators

ADD:                '+';
SUB:                '-';
MUL:                '*';
DIV:                '/';
MOD:                '%';

EQUAL:              '==';
NOTEQUAL:           '!=';
GT:                 '>';
LT:                 '<';
LE:                 '<=';
GE:                 '>=';

AND:                '&&';
OR:                 '||';
BANG:               '!';

LSHIFT:             '<<';
RSHIFT:             '>>';
URSHIFT:            '>>>';

BITAND:             '&';
BITOR:              '|';
TILDE:              '~';
CARET:              '^';

ASSIGN:             '=';
ADD_ASSIGN:         '+=';
SUB_ASSIGN:         '-=';
MUL_ASSIGN:         '*=';
DIV_ASSIGN:         '/=';
MOD_ASSIGN:         '%=';

AND_ASSIGN:         '&&=';
OR_ASSIGN:          '||=';

BITAND_ASSIGN:      '&=';
BITOR_ASSIGN:       '|=';
BITXOR_ASSIGN:      '^=';

LSHIFT_ASSIGN:      '<<=';
RSHIFT_ASSIGN:      '>>=';
URSHIFT_ASSIGN:     '>>>=';

// Whitespace and comments

WS:                 [ \t\r\n\u000C]+ -> channel(HIDDEN);
COMMENT:            '/*' (COMMENT|.)*? '*/' -> channel(HIDDEN) ;
LINE_COMMENT:       '//' ~[\r\n]*    -> channel(HIDDEN);

// Identifiers
IDENTIFIER:         Letter LetterOrDigit*;

// Fragment rules
fragment ExponentPart
    : [eE] [+-]? Digits
    ;

fragment EscapeSequence
    : '\\' [btnfr"'\\]
    | '\\' ([0-3]? [0-7])? [0-7]
    | '\\' 'u'+ HexDigit HexDigit HexDigit HexDigit
    ;

fragment HexDigits
    : HexDigit ((HexDigit | '_')* HexDigit)?
    ;

fragment HexDigit
    : [0-9a-fA-F]
    ;

fragment Digits
    : [0-9] ([0-9_]* [0-9])?
    ;

fragment LetterOrDigit
    : Letter
    | [0-9]
    ;

fragment Letter
    : [a-zA-Z$_]
    | ~[\u0000-\u007F\uD800-\uDBFF]
    | [\uD800-\uDBFF] [\uDC00-\uDFFF]
    ;
