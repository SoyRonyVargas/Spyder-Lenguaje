import re

# Definición de los tokens
tokens = [
    ('KEYWORD', r'\b(if|else|print|scan)\b'),  # Palabras clave
    ('OPERATOR', r'(\+|\-|\*|\/|==|<=|>=|=)'),  # Operadores (incluyendo asignación =)
    ('IDENTIFIER', r'\b[A-Za-z_][A-Za-z0-9_]*\b'),  # Identificadores (nombres de variables)
    ('NUMBER', r'\b\d+(\.\d+)?\b'),  # Números (enteros y flotantes)
    ('STRING', r'\".*?\"'),  # Cadenas de texto
    ('SYMBOL', r'[!()\{\}]'),  # Símbolos como (), {}, !
    ('WHITESPACE', r'\s+'),  # Espacios en blanco
    ('NEWLINE', r'!')  # Fin de línea
]

allowed_characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_!\"#%&'()*+,-./:;<=>?@[\\]^`{|}~ "

# Validación de caracteres permitidos en el código fuente
def validate_characters(code):
    for char in code:
        if char not in allowed_characters:
            print(char)
            raise SyntaxError(f"Carácter no permitido '{char}' encontrado en el código.")

# Función para el analizador léxico
def lexer(code):
    validate_characters(code)  # Validar caracteres antes del análisis léxico
    pos = 0
    tokens_found = []
    
    while pos < len(code):
        match = None
        for token_type, token_regex in tokens:
            pattern = re.compile(token_regex)
            match = pattern.match(code, pos)
            if match:
                token_value = match.group(0)
                if token_type != 'WHITESPACE':  # Ignorar espacios en blanco
                    tokens_found.append((token_type, token_value))
                pos = match.end(0)
                break
        if not match:
            try:
                # print(pos)
                # print(code[pos])
                raise SyntaxError(f'Error léxico en la posición {pos}: {code[pos]}')
            except SyntaxError as e:
                print(e)
                break
    return tokens_found

# Tabla de símbolos (almacena variables y sus valores)
symbol_table = {}

# Función para evaluar expresiones aritméticas
def evaluate_expression(tokens):
    # Creamos una expresión matemática como una cadena para que Python la evalúe
    expr = ""
    for token_type, token_value in tokens:
        if token_type in ('IDENTIFIER'):
            if token_value in symbol_table:
                expr += str(symbol_table[token_value])
            else:
                raise SyntaxError(f'Variable no definida: {token_value}')
        elif token_type in ('NUMBER',  'STRING', 'OPERATOR'):
            expr += token_value
        else:
            raise SyntaxError(f'Error de sintaxis en la expresión: {token_value}')
    # Evaluamos la expresión usando eval
    try:
        print("expr")
        print(expr)
        result = eval(expr)
    except Exception as e:
        raise SyntaxError(f'Error evaluando la expresión: {expr} ({e})')
    return result

# Función para procesar asignaciones de variables
def parse_assignment(tokens):
    # Esperamos un formato: IDENTIFICADOR = EXPR
    if len(tokens) >= 3 and tokens[0][0] == 'IDENTIFIER' and tokens[1][0] == 'OPERATOR' and tokens[1][1] == '=':
        var_name = tokens[0][1]  # Nombre de la variable
        expr_tokens = tokens[2:]  # La expresión o valor que se asignará
        print('expr_tokens')
        print(expr_tokens)
        print(f'Variable detectada: {var_name}')
        
        # Evaluar la expresión matemática o valor literal
        if len(expr_tokens) == 1 and expr_tokens[0][0] == 'NUMBER':
            # Asignación simple de un número
            value = float(expr_tokens[0][1]) if '.' in expr_tokens[0][1] else int(expr_tokens[0][1])
        elif len(expr_tokens) == 1 and expr_tokens[0][0] == 'STRING':
            # Asignación de una cadena
            value = expr_tokens[0][1].strip('"')
        else:
            # Evaluación de una expresión matemática
            value = evaluate_expression(expr_tokens)
        
        # Almacenar la variable en la tabla de símbolos
        symbol_table[var_name] = value
        print(f'Variable asignada: {var_name} = {value}')
    else:
        raise SyntaxError('Error de sintaxis en la asignación.')

# Ejemplo de código fuente en el nuevo lenguaje
code = '''
hola = 5!

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

# Mostrar las variables almacenadas
print("Variables almacenadas:")
print(symbol_table)
