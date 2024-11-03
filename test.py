import re

# Definición de los tokens
tokens = [
    ('START', r'\bINICIO\b'),                      # Inicio del programa
    ('END', r'\bFIN\b'),                           # Fin del programa
    ('KEYWORD', r'\b(if|else|print|scan)\b'),      # Palabras clave
    ('OPERATOR', r'(\+|\-|\*|\/|==|<=|>=|>|<|=)'), # Operadores
    ('IDENTIFIER', r'\b[A-Za-z_][A-Za-z0-9_]*\b'), # Identificadores
    ('NUMBER', r'\b\d+(\.\d+)?\b'),                # Números (enteros y flotantes)
    ('STRING', r'\".*?\"'),                        # Cadenas de texto
    ('SYMBOL', r'[!()\{\}]'),                      # Símbolos como (), {}, !
    ('COMMENT', r'#.*'),                           # Comentarios
    ('WHITESPACE', r'\s+'),                        # Espacios en blanco
    ('NEWLINE', r'!')                              # Fin de línea
]

# Función para el analizador léxico
def lexer(code):
    pos = 0
    tokens_found = []
    minified_code = ""  # Para almacenar el código sin comentarios ni espacios en blanco
    
    while pos < len(code):
        match = None
        for token_type, token_regex in tokens:
            pattern = re.compile(token_regex)
            match = pattern.match(code, pos)
            if match:
                token_value = match.group(0)
                if token_type != 'WHITESPACE' and token_type != 'COMMENT':  # Ignorar espacios en blanco y comentarios
                    tokens_found.append((token_type, token_value))  # Guardamos el token encontrado
                    minified_code += token_value  # Construimos el código minificado
                pos = match.end(0)
                break
        if not match:
            raise SyntaxError(f'Error léxico en la posición {pos}: "{code[pos]}"')
    return tokens_found, minified_code

# Ejemplo de uso
code = """
INICIO
x = 10!
if x > 5!
else y = 20!
FIN
"""

try:
    tokens_detected, minified_code = lexer(code)
    print("Tokens detectados:", tokens_detected)
    print("Código minificado:", minified_code)
    print()
except SyntaxError as e:
    print(str(e))
