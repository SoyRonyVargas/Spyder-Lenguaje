import re

# Definición de los tokens
tokens = [
    ('KEYWORD', r'\b(if|else|print|scan)\b'),       # Palabras clave
    ('OPERATOR', r'(\+|\-|\*|\/|==|<=|>=|=)'),      # Operadores (incluyendo asignación =)
    ('IDENTIFIER', r'\b[A-Za-z_][A-Za-z0-9_]*\b'),  # Identificadores (nombres de variables)
    ('NUMBER', r'\b\d+(\.\d+)?\b'),                 # Números (enteros y flotantes)
    ('STRING', r'\".*?\"'),                         # Cadenas de texto
    ('SYMBOL', r'[!()\{\}]'),                       # Símbolos como (), {}, !
    ('COMMENT', r'#.*'),                            # Comentarios que empiezan con #
    ('WHITESPACE', r'\s+'),                         # Espacios en blanco
    ('NEWLINE', r'!')                               # Fin de línea
]

# Función para el analizador léxico
def lexer(code):
    pos = 0
    tokens_found = []
    
    while pos < len(code):
        match = None
        for token_type, token_regex in tokens:
            pattern = re.compile(token_regex)
            match = pattern.match(code, pos)
            if match:
                token_value = match.group(0)
                if token_type != 'WHITESPACE' and token_type != 'COMMENT':  # Ignorar espacios en blanco y comentarios
                    tokens_found.append((token_type, token_value))
                pos = match.end(0)
                break
        if not match:
            raise SyntaxError(f'Error léxico en la posición {pos}: "{code[pos]}"')
    return tokens_found

# Tabla de símbolos (almacena variables y sus valores)
symbol_table = {}

# Función para evaluar expresiones aritméticas
def evaluate_expression(tokens):
    expr = ""
    for token_type, token_value in tokens:
        if token_type == 'IDENTIFIER':
            if token_value in symbol_table:
                expr += str(symbol_table[token_value])
            else:
                raise SyntaxError(f'Variable no definida: {token_value}')
        elif token_type in ('NUMBER', 'STRING', 'OPERATOR'):
            expr += token_value
        else:
            raise SyntaxError(f'Error de sintaxis en la expresión: {token_value}')
    try:
        result = eval(expr)
    except Exception as e:
        raise SyntaxError(f'Error evaluando la expresión: {expr} ({e})')
    return result

# Función para procesar asignaciones de variables
def parse_assignment(tokens):
    if len(tokens) >= 3 and tokens[0][0] == 'IDENTIFIER' and tokens[1][0] == 'OPERATOR' and tokens[1][1] == '=':
        var_name = tokens[0][1]  # Nombre de la variable
        expr_tokens = tokens[2:]  # La expresión o valor que se asignará
        
        # Evaluar la expresión matemática o valor literal
        if len(expr_tokens) == 1 and expr_tokens[0][0] == 'NUMBER':
            value = float(expr_tokens[0][1]) if '.' in expr_tokens[0][1] else int(expr_tokens[0][1])
        elif len(expr_tokens) == 1 and expr_tokens[0][0] == 'STRING':
            value = expr_tokens[0][1].strip('"')
        else:
            value = evaluate_expression(expr_tokens)
        
        # Almacenar la variable en la tabla de símbolos
        symbol_table[var_name] = value
    else:
        raise SyntaxError('Error de sintaxis en la asignación.')

# Ejemplo de código fuente en el nuevo lenguaje con un caso de error
code = '''
z = 2!
x = 22! # Esto es un comentario
'''

# Ejecutamos el lexer
tokens_detected = lexer(code)

# Procesar asignaciones
current_statement = []
for token in tokens_detected:
    print(token)
    if token[1] == '!':  # Si encontramos un fin de línea, procesamos la asignación
        parse_assignment(current_statement)
        current_statement = []
    else:
        current_statement.append(token)

# Validar que la última declaración haya terminado con '!'
if current_statement:
    raise SyntaxError('Error de sintaxis: falta el símbolo "!" al final de la declaración.')

# Mostrar las variables almacenadas
print("Variables almacenadas:")
print(symbol_table)
