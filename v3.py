from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

# Definición de los tokens
tokens = [
    ('START', r'\bINICIO\b'),                      # Inicio del programa
    ('END', r'\bFIN\b'),                           # Fin del programa
    ('KEYWORD', r'\b(if|else|print|scan)\b'),      # Palabras clave
    ('OPERATOR', r'(\+|\-|\*|\/|==|<=|>=|=|%|<|>|&|\|)'),  # Operadores
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
    line_num = 1  # Contador de línea
    tokens_found = []
    minified_code = ""
    
    while pos < len(code):
        match = None
        for token_type, token_regex in tokens:
            pattern = re.compile(token_regex)
            match = pattern.match(code, pos)
            if match:
                token_value = match.group(0)
                if token_type != 'WHITESPACE' and token_type != 'COMMENT':
                    tokens_found.append((token_type, token_value, line_num))  # Añadimos el número de línea
                    minified_code += token_value
                if token_type == 'NEWLINE':
                    line_num += 1  # Incrementamos la línea en caso de 'NEWLINE'
                pos = match.end(0)
                line_num += token_value.count('!')  # Incrementamos la línea por cada '!'
                break
        if not match:
            raise SyntaxError(f'Error léxico en la línea {line_num}, posición {pos}: "{code[pos]}"')
    return tokens_found, minified_code

# Función para procesar el programa en zonas de inicio y fin
def parse_program(tokens):
    if tokens[0][0] != 'START' or tokens[-1][0] != 'END':
        raise SyntaxError('El programa debe comenzar con "INICIO" y terminar con "FIN".')
    
    in_program = False
    symbol_table = {}
    current_statement = []
    
    for token in tokens:
        if token[0] == 'START':
            in_program = True
        elif token[0] == 'END':
            in_program = False
            if current_statement:
                line_num = current_statement[-1][2]
                raise SyntaxError(f'Error de sintaxis en la línea {line_num}: falta el símbolo "!" al final de la declaración.')
            break
        elif in_program:
            if token[1] == '!':
                parse_assignment(current_statement, symbol_table)
                current_statement = []
            else:
                current_statement.append(token)

    if in_program:
        raise SyntaxError('Error de sintaxis: el programa no ha sido cerrado correctamente con "FIN".')
    
    return symbol_table

# Función para procesar asignaciones de variables
def parse_assignment(tokens, symbol_table):
    if len(tokens) >= 3 and tokens[0][0] == 'IDENTIFIER' and tokens[1][0] == 'OPERATOR' and tokens[1][1] == '=':
        var_name = tokens[0][1]
        expr_tokens = tokens[2:]

        if len(expr_tokens) == 1 and expr_tokens[0][0] == 'NUMBER':
            value = float(expr_tokens[0][1]) if '.' in expr_tokens[0][1] else int(expr_tokens[0][1])
        elif len(expr_tokens) == 1 and expr_tokens[0][0] == 'STRING':
            value = expr_tokens[0][1].strip('"')
        else:
            filterByIdentifiers = filter(lambda x: x[0] == 'IDENTIFIER', expr_tokens)
            for(_, token_value, line_num) in filterByIdentifiers:
                if token_value not in symbol_table:
                    raise SyntaxError(f'Error de sintaxis en la línea {line_num}: falta el símbolo "!" al final de la declaración.')
            value = evaluate_expression(expr_tokens, symbol_table)

        symbol_table[var_name] = value
    else:
        line_num = tokens[0][2] if tokens else '?'
        raise SyntaxError(f'Error de sintaxis en la línea {line_num} en la asignación.')

# Función para evaluar expresiones aritméticas
def evaluate_expression(tokens, symbol_table):
    expr = ""
    for token_type, token_value, line_num in tokens:
        if token_type == 'IDENTIFIER':
            if token_value in symbol_table:
                expr += str(symbol_table[token_value])
            else:
                raise SyntaxError(f'Variable no definida en la línea {line_num}: {token_value}')
        elif token_type in ('NUMBER', 'STRING', 'OPERATOR'):
            expr += token_value
        else:
            raise SyntaxError(f'Error de sintaxis en la expresión en la línea {line_num}: {token_value}')
    try:
        result = eval(expr)
    except Exception as e:
        raise SyntaxError(f'Error evaluando la expresión: {expr} ({e})')
    return result

@app.route('/compile', methods=['POST'])
def compile_code():
    code = request.json.get('code', '').strip()
    
    if not code:
        return jsonify({'error': 'El código no puede estar vacío.'}), 400
    
    try:
        tokens_detected, minified_code = lexer(code)
        symbol_table = parse_program(tokens_detected)

        return jsonify({
            'message': 'Compilado con éxito.',
            'variables': symbol_table,
            'minified_code': minified_code,
            'tokens_found': tokens_detected
        })
    
    except SyntaxError as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
