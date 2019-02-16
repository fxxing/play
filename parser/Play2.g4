grammar Play;

compilationUnit
    : importDeclaration* modifiedMember* EOF
    ;
modifiedMember
    : modifier* memberDeclaration
    ;
memberDeclaration
    : classDeclaration
    | methodDeclaration
    | variableDeclaration
    ;
qualifiedName
    : IDENTIFIER ('.' IDENTIFIER)*
    ;
qualifiedNameList
    : qualifiedName (',' qualifiedName)*
    ;
modifier
    : 'public'
    | 'private'
    | 'protected'
    | 'static'
    | annotation
    ;
type
    : 'boolean'
    | 'byte'
    | 'short'
    | 'int'
    | 'long'
    | 'float'
    | 'double'
    | 'void'
    | classType
    ;
literal
    : DECIMAL_LITERAL
    | HEX_LITERAL
    | OCT_LITERAL
    | BINARY_LITERAL
    | FLOAT_LITERAL
    | HEX_FLOAT_LITERAL
    | BYTE_LITERAL
    | STRING_LITERAL
    | BOOL_LITERAL
    | NULL_LITERAL
    ;
// ==============================================================================================
// import
// ==============================================================================================
importDeclaration
    : 'import' (qualifiedName '.')? importName (',' importName)*
    ;
importName
    : IDENTIFIER 'as' IDENTIFIER
    | IDENTIFIER
    | '*'
    ;
// ==============================================================================================
// class
// ==============================================================================================
classDeclaration
    : ('class' | 'interface' | 'annotation') IDENTIFIER genericParameters? (':' classTypeList)? classBody
    ;
classBodyDeclaration
    : 'static' block
    | modifiedMember
    ;
classTypeList
    : classType (',' classType)*
    ;
classType
    : qualifiedName genericArguments? classTypeSuffix*
    ;
classTypeSuffix
    :'.' IDENTIFIER genericArguments?
    ;
// ==============================================================================================
// generic
// ==============================================================================================
genericParameters
    : '<' genericParameter (',' genericParameter)* '>'
    ;
genericParameter
    : IDENTIFIER (':' classType)?
    ;
genericArguments
    : '<' genericArgument (',' genericArgument)* '>'
    ;
genericArgument
    : classType
    | '*' (':' classType)?
    ;
// ==============================================================================================
// method
// ==============================================================================================
// TOXDO allow extention
methodDeclaration
    : 'def' genericParameters? IDENTIFIER '(' formalParameterList? ')' methodResults? ('throws' classTypeList)? block?
    ;
methodResults
    : '->' type+
    ;
formalParameterList
    : formalParameter (',' formalParameter)* (',' lastFormalParameter)?
    | lastFormalParameter
    ;
formalParameter
    : modifier* variableDeclaratorId ('=' expression)?
    ;
lastFormalParameter
    : modifier* IDENTIFIER ':' type '*'
    ;
arguments
    : argument (',' argument)*
    ;
argument
    : (IDENTIFIER '=')? expression
    | (IDENTIFIER '=')? annotation
    ;
// ==============================================================================================
// annotation
// ==============================================================================================
annotation
    : '@' qualifiedName ('(' arguments ')')?
    ;
variableDeclaration
    : ('var'|'val') variableDeclaratorIdList ('=' expression+)?
    ;
variableDeclaratorId
    : IDENTIFIER (':' type)?
    ;
variableDeclaratorIdList
    : variableDeclaratorId (',' variableDeclaratorId)*
    ;
// ==============================================================================================
// statement
// ==============================================================================================
block
    : '{' statement* '}'
    ;
statement
    : forStatement
    | whileStatement
    | doWhileStatement
    | returnStatement
    | throwStatement
    | breakStatement
    | continueStatement
    | assignStatement
    | expression
    | block
    | yieldStatement
    ;
forStatement
    : 'for' IDENTIFIER 'in' expression ('if' expression)? block
    ;
whileStatement
    : 'while' expression block
    ;
doWhileStatement
    : 'do' block 'while' expression
    ;
returnStatement
    : 'return' expressionList?
    ;
throwStatement
    : 'throw' expression?
    ;
breakStatement
    : 'break'
    ;
continueStatement
    : 'continue'
    ;
assignStatement
    : ('var'|'val')? variableDeclaratorIdList bop=('=' | '+=' | '-=' | '*=' | '/=' | '%=' | '&=' | '|=' | '^=' | '&&=' | '||=' | '>>=' | '>>>=' | '<<=') expressionList
    ;
yieldStatement
    : (('var'|'val')? variableDeclaratorIdList '=' )? 'yield' expressionList?
    ;
// ==============================================================================================
// expression
// ==============================================================================================
// TOXDO split this to force precedence, not use built-in resoluation method
expression
    : primary
    | expression '.' ( IDENTIFIER | methodCall | 'this'| 'super' | classCreation)
    | expression '[' slice ']'
    | ifExpression
    | methodCall
    | classCreation
    | expression rop='in' expression
    | expression 'as' type
    | prefix=('+'|'-') expression
    | prefix=('~'|'!') expression
    | expression bop=('*'|'/'|'%') expression
    | expression bop=('+'|'-') expression
    | expression bop=('<<' | '>>>' | '>>') expression
    | expression rop=('<=' | '>=' | '>' | '<' | '==' | '!=' | 'is') expression
    | expression bop='&' expression
    | expression bop='^' expression
    | expression bop='|' expression
    | expression rop='&&' expression
    | expression rop='||' expression
    | lambdaExpression
    | expression '::' IDENTIFIER genericArguments?
    | classType '::' ('new'| IDENTIFIER genericArguments?)
    | tryExpression
    | listLiteral
    | setLiteral
    | dictLiteral
    | listComprehension
    | setComprehension
    | dictComprehension
    | matchExpression
    ;
expressionList
    : expression (',' expression) *
    ;
ifExpression
    : 'if' expression block elifClause* elseClause?
    ;
elifClause
    : 'elseif' expression block
    ;
elseClause
    : 'else' block
    ;
tryExpression
    : 'try' resourceSpecification? block (catchClause+ finallyBlock? | finallyBlock)
    ;
finallyBlock
    : 'finally' block
    ;
resourceSpecification
    : resource (',' resource)*
    ;
resource
    : variableDeclaratorId '=' expression
    ;
catchClause
    : 'catch' (IDENTIFIER ':' qualifiedName ('|' qualifiedName)*)? block
    ;
classCreation
    : 'new' qualifiedClassName ('.' qualifiedClassName)* '(' arguments? ')' classBody?
    ;
qualifiedClassName
    :IDENTIFIER genericArguments?
    ;
classBody
    : '{' classBodyDeclaration* '}'
    ;
methodCall
    : (IDENTIFIER | 'this' | 'super') '(' arguments? ')'
    ;
matchExpression
    : 'match' expression? '{' matchClause+ '}'
    ;
matchClause
    : ('else' | expression) '->' (expression | block)
    ;
primary
    : '(' expression ')'
    | 'this'
    | 'super'
    | literal
    | IDENTIFIER
    | type '.' 'class'
    ;
lambdaExpression
    : lambdaParameters '->' lambdaBody
    | '{' expression '}'
    ;
lambdaParameters
    : formalParameter
    | formalParameterList
    | '(' formalParameterList? ')'
    ;
lambdaBody
    : expression
    | block
    ;

// ==============================================================================================
// built in types
// ==============================================================================================
slice
    : expression (':' expression (':' expression)?)?
    ;
listLiteral
    : '[' expressionList? ','? ']'
    ;
setLiteral
    : '{' expressionList? ','? '}'
    ;
dictLiteral
    : '{' dictItemList? ','? '}'
    ;
dictItemList
    : dictItem (',' dictItem)*
    ;
dictItem
    : expression ':' expression
    ;
listComprehension
    : '[' expressionList comprehension+ ']'
    ;
setComprehension
    : '{' expressionList comprehension+ '}'
    ;
dictComprehension
    : '{' expressionList ':' expressionList comprehension+ '}'
    ;
comprehension
    : 'for' variableDeclaratorIdList 'in' expression ('if' expression)?
    ;
// ==============================================================================================
// tokens
// ==============================================================================================

// Keywords

AS:                 'as';

BOOLEAN:            'boolean';
BYTE:               'byte';
SHORT:              'short';
INT:                'int';
LONG:               'long';
FLOAT:              'float';
DOUBLE:             'double';
VOID:               'void';

IMPORT:             'import';
CLASS:              'class';
INTERFACE:          'interface';
ANNOTATION:         'annotation';
DEF:                'def';
STATIC:             'static';

THIS:               'this';
SUPER:              'super';

PRIVATE:            'private';
PROTECTED:          'protected';
PUBLIC:             'public';

IF:                 'if';
ELSE:               'else';
ELSEIF:             'elseif';
FOR:                'for';
IN:                 'in';
DO:                 'do';
WHILE:              'while';
BREAK:              'break';
CONTINUE:           'continue';
RETURN:             'return';
TRY:                'try';
CATCH:              'catch';
FINALLY:            'finally';
THROW:              'throw';
THROWS:             'throws';
MATCH:              'match';
YIELD:              'yield';

IS:                 'is';
NEW:                'new';
VAR:                'var';
VAL:                'val';

// Literals

DECIMAL_LITERAL:    ('0' | [1-9] (Digits? | '_'+ Digits)) [lL]?;
HEX_LITERAL:        '0' [xX] [0-9a-fA-F] ([0-9a-fA-F_]* [0-9a-fA-F])? [lL]?;
OCT_LITERAL:        '0' '_'* [0-7] ([0-7_]* [0-7])? [lL]?;
BINARY_LITERAL:     '0' [bB] [01] ([01_]* [01])? [lL]?;

FLOAT_LITERAL:      (Digits '.' Digits? | '.' Digits) ExponentPart? [fFdD]?
             |       Digits (ExponentPart [fFdD]? | [fFdD])
             ;

HEX_FLOAT_LITERAL:  '0' [xX] (HexDigits '.'? | HexDigits? '.' HexDigits) [pP] [+-]? Digits [fFdD]?;

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
