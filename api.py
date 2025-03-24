from flask import Flask, request, jsonify
from deep_translator import GoogleTranslator
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

# Definición de los tokens
tokens = [
    ('START', r'\bINICIO\b'),                      # Inicio del programa
    ('END', r'\bFIN\b'),                           # Fin del programa
    ('KEYWORD', r'\b(if|else|print|scan|while|doFor|func)\b'),# Palabras clave
    ('OPERATOR', r'(\+|\-|\*|\/|==|<=|>=|=|%|<|>|&|\|)'),  # Operadores
    ('IDENTIFIER', r'\b[A-Za-z_][A-Za-z0-9_]*\b'), # Identificadores
    ('NUMBER', r'\b\d+(\.\d+)?\b'),                # Números (enteros y flotantes)
    ('STRING', r'\".*?\"'),                        # Cadenas de texto
    ('SYMBOL', r'[!()\{\};]'),                      # Símbolos como (), {}, !
    ('COMMENT', r'#.*'),                           # Comentarios
    ('WHITESPACE', r'\s+'),                        # Espacios en blanco
    ('NEWLINE', r'!'),                              # Fin de línea
    ('LBRACE', r'\{'),  # Llave izquierda
    ('RBRACE', r'\}'),  # Llave derecha
    ('SYMBOL', r'[!()]'),  # Símbolos restantes (quita { y } de aquí)
]

logs = []
unused_vars = {}
unused_fns = {}
types = {}

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

def parse_program(tokens):
    if tokens[0][0] != 'START' or tokens[-1][0] != 'END':
        raise SyntaxError('El programa debe comenzar con "INICIO" y terminar con "FIN".')
    
    in_program = False
    symbol_table = {
        '__funciones__': {},  # Nuevo: almacenar funciones
        '__logs__': {},  # Nuevo: almacenar funciones
    }
    current_statement = []
    brace_stack = []  # Para manejar bloques anidados
    
    for token in tokens:
        if token[0] == 'START':
            in_program = True
        elif token[0] == 'END':
            in_program = False
            if current_statement:
                line_num = current_statement[-1][2]
                raise SyntaxError(f'Error de sintaxis en la línea {line_num}: falta el símbolo "!" al final.')
            break
        elif in_program:
            if token[1] == '!':
                if not brace_stack:  # Solo procesar si no estamos dentro de un bloque
                    parse_statement(current_statement, symbol_table)
                    current_statement = []
                else:
                    current_statement.append(token)
            elif token[1] == '{':
                brace_stack.append('{')
                current_statement.append(token)
            elif token[1] == '}':
                if not brace_stack:
                    raise SyntaxError(f'Llave de cierre sin apertura en línea {token[2]}')
                brace_stack.pop()
                current_statement.append(token)
                if not brace_stack:  # Fin del bloque
                    parse_statement(current_statement, symbol_table)
                    current_statement = []
            else:
                current_statement.append(token)

    if in_program:
        raise SyntaxError('El programa no ha sido cerrado con "FIN".')
    
    return symbol_table

def parse_statement(tokens, symbol_table):
    if not tokens:
        return
    
    first_token = tokens[0][1]
    if first_token == 'if':
        parse_if(tokens, symbol_table)
    elif first_token == 'else':
        parse_else(tokens, symbol_table)
    elif first_token == 'while':  # Nuevo caso para while
        parse_while(tokens, symbol_table)
    elif first_token == 'doFor':  # Nuevo caso para doFor
        parse_doFor(tokens, symbol_table)
    elif first_token == 'print':  # Nuevo caso para print
        parse_print(tokens, symbol_table)
    elif first_token == 'func':
        parse_function(tokens, symbol_table)
    elif tokens[0][1] == '{':
        parse_block(tokens, symbol_table)
    else:
        if len(tokens) > 1 and tokens[1][1] == '(':
            parse_function_call(tokens, symbol_table)
        else:
            parse_assignment(tokens, symbol_table)

def parse_function(tokens, symbol_table):
    try:
        # Validar estructura básica: 'func' + IDENTIFIER + '('
        if len(tokens) < 4:
            line_num = tokens[0][2]
            raise SyntaxError(f'Error en línea {line_num}: Declaración de función incompleta')
            
        if tokens[1][0] != 'IDENTIFIER':
            line_num = tokens[1][2]
            raise SyntaxError(f'Error en línea {line_num}: Nombre de función no válido')
            
        if tokens[2][1] != '(':
            line_num = tokens[2][2]
            raise SyntaxError(f'Error en línea {line_num}: Se esperaba "(" después del nombre de la función')
        
        func_name = tokens[1][1]
        
        # Buscar cierre de parámetros
        paren_end = None
        paren_count = 0
        for i, token in enumerate(tokens[2:]):
            if token[1] == '(':
                paren_count += 1
            elif token[1] == ')':
                paren_count -= 1
                if paren_count == 0:
                    paren_end = i + 2  # Ajustar índice por el slice
                    break
        
        if paren_end is None:
            line_num = tokens[0][2]
            raise SyntaxError(f'Error en línea {line_num}: Paréntesis de parámetros no cerrado')
        
        # Extraer parámetros
        params = []
        for t in tokens[3:paren_end]:
            if t[0] == 'IDENTIFIER':
                params.append(t[1])
            elif t[1] != ',':
                line_num = t[2]
                raise SyntaxError(f'Error en línea {line_num}: Carácter no válido en parámetros')
        
        # Validar cuerpo
        body_start = paren_end + 1
        if body_start >= len(tokens) or tokens[body_start][1] != '{':
            line_num = tokens[body_start][2] if body_start < len(tokens) else tokens[-1][2]
            raise SyntaxError('Error en línea {line_num}: Cuerpo de función debe comenzar con {')
        
        # Almacenar función
        symbol_table['__funciones__'][func_name] = {
            'params': params,
            'body': tokens[body_start:]
        }

        unused_fns[func_name] = {
            'params': params,
            'body': tokens[body_start:],
            'called': False,  # Nuevo: indica si la función fue llamada
            # 'used_params': used_params  # Parámetros realmente usados
        }

    except ValueError:
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: Estructura de función inválida')
# Nueva función para procesar llamadas a funciones
def parse_function_call(tokens, symbol_table):
    func_name = tokens[0][1]
    
    # print(symbol_table)

    if func_name not in symbol_table['__funciones__'] or not isinstance(symbol_table['__funciones__'][func_name], dict):
        raise SyntaxError(f'Función no definida: {func_name}')
    
    # Obtener argumentos
    paren_start = tokens.index(('SYMBOL', '(', tokens[0][2]))
    paren_end = tokens.index(('SYMBOL', ')', tokens[0][2]))
    args_tokens = tokens[paren_start+1:paren_end]
    
    # Evaluar argumentos
    args = []
    current_arg = []
    for token in args_tokens:
        if token[1] == ',':
            args.append(evaluate_expression(current_arg, symbol_table))
            current_arg = []
        else:
            current_arg.append(token)
    if current_arg:
        args.append(evaluate_expression(current_arg, symbol_table))
    
    # Verificar parámetros
    func_data = symbol_table['__funciones__'][func_name]
    if len(args) != len(func_data['params']):
        raise SyntaxError(f'Número incorrecto de argumentos para {func_name}')
    
    # Crear nuevo ámbito
    local_scope = symbol_table.copy()
    local_scope.update(zip(func_data['params'], args))
    
    # Ejecutar cuerpo de la función
    parse_block(func_data['body'], local_scope)
    
    # # Actualizar símbolos globales
    # for var in local_scope:
    #     if var not in symbol_table:
    #         symbol_table[var] = local_scope[var]
    unused_fns[func_name]['called'] = True



def parse_print(tokens, symbol_table):
    try:
        # Buscar paréntesis de la expresión
        paren_start = tokens.index(('SYMBOL', '(', tokens[0][2]))
        paren_end = tokens.index(('SYMBOL', ')', tokens[0][2]))
    except ValueError:
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: print debe tener la forma print(expresión).')
    
    # Evaluar la expresión dentro del print
    expr_tokens = tokens[paren_start+1:paren_end]
    result = evaluate_expression(expr_tokens, symbol_table)
    
    # Almacenar el resultado en el array global
    print(result)
    logs.append(str(result))

def parse_doFor(tokens, symbol_table):
    # Validar estructura básica
    if len(tokens) < 2 or tokens[1][1] != '(':
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: estructura "doFor" debe ser: doFor (inicialización; condición; actualización) {{...}}')

    try:
        # Buscar paréntesis de condición
        paren_start = tokens.index(('SYMBOL', '(', tokens[0][2]), 1)  # Busca "(" después de "doFor"
        paren_end = tokens.index(('SYMBOL', ')', tokens[0][2]))
    except ValueError:
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: paréntesis mal formados en "doFor".')
    
    # Obtener las tres partes del for
    for_parts = tokens[paren_start+1:paren_end]
    parts = []
    current_part = []
    
    for token in for_parts:
        if token[1] == ';':
            parts.append(current_part)
            current_part = []
        else:
            current_part.append(token)
    parts.append(current_part)
    
    if len(parts) != 3:
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: "doFor" necesita tres partes separadas por ";".')
    
    init_tokens, condition_tokens, update_tokens = parts
    
    # Procesar inicialización (asignación)
    parse_assignment(init_tokens, symbol_table)
    
    # Evaluar condición (debe ser booleana)
    condition = evaluate_expression(condition_tokens, symbol_table)
    if not isinstance(condition, bool):
        line_num = tokens[0][2]
        raise SyntaxError(f'Condición no booleana en línea {line_num} en "doFor".')
    
    # Procesar cuerpo del doFor (debe estar entre llaves)
    body_tokens = tokens[paren_end+1:]
    if not body_tokens or body_tokens[0][1] != '{':
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: cuerpo del "doFor" debe estar entre llaves {{}}.')
    
    # Ejecutar el bucle
    while condition:
        parse_block(body_tokens, symbol_table)
        parse_assignment(update_tokens, symbol_table)
        condition = evaluate_expression(condition_tokens, symbol_table)

def parse_while(tokens, symbol_table):
    try:
        # Buscar paréntesis de condición
        cond_start = tokens.index(('SYMBOL', '(', tokens[0][2])) + 1
        cond_end = tokens.index(('SYMBOL', ')', tokens[0][2]))
    except ValueError:
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: paréntesis mal formados en "while".')
    
    # Evaluar condición
    condition = evaluate_expression(tokens[cond_start:cond_end], symbol_table)
    if not isinstance(condition, bool):
        line_num = tokens[0][2]
        raise SyntaxError(f'Condición no booleana en línea {line_num} (se esperaba true/false).')
    
    # Procesar cuerpo (debe estar entre llaves)
    body_tokens = tokens[cond_end+1:]
    if not body_tokens or body_tokens[0][1] != '{':
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: cuerpo del "while" debe estar entre llaves {{}}.')
    
    parse_block(body_tokens, symbol_table)

def parse_block(tokens, symbol_table):
    if tokens[0][1] != '{' or tokens[-1][1] != '}':
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: bloque mal formado.')
    
    current_statement = []
    brace_count = 0  # Contador de bloques anidados
    
    for token in tokens[1:-1]:  # Ignorar las llaves externas
        if token[1] == '{':
            brace_count += 1
        elif token[1] == '}':
            brace_count -= 1
        
        # Procesar "!" solo si no estamos dentro de un bloque anidado
        if token[1] == '!' and brace_count == 0:
            parse_statement(current_statement, symbol_table)
            current_statement = []
        else:
            current_statement.append(token)
    
    if current_statement:
        line_num = current_statement[-1][2]
        raise SyntaxError(f'Error en línea {line_num}: falta "!" al final.')
    
def parse_if(tokens, symbol_table):
    try:
        # Buscar paréntesis de condición
        cond_start = tokens.index(('SYMBOL', '(', tokens[0][2])) + 1
        cond_end = tokens.index(('SYMBOL', ')', tokens[0][2]))
    except ValueError:
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: paréntesis mal formados en "if".')
    
    # Evaluar condición
    condition = evaluate_expression(tokens[cond_start:cond_end], symbol_table)
    if not isinstance(condition, bool):
        line_num = tokens[0][2]
        raise SyntaxError(f'Condición no booleana en línea {line_num}')
    
    # Procesar cuerpo del if SOLO si la condición es verdadera
    body_tokens = tokens[cond_end+1:]
    if condition:  # <--- ¡Aquí está el cambio clave!
        if not body_tokens or body_tokens[0][1] != '{':
            line_num = tokens[0][2]
            raise SyntaxError(f'Error en línea {line_num}: cuerpo del "if" debe estar entre llaves.')
        parse_block(body_tokens, symbol_table)

def parse_else(tokens, symbol_table):
    if len(tokens) < 2:
        line_num = tokens[0][2]
        raise SyntaxError(f'Error en línea {line_num}: "else" no puede estar vacío.')
    # Procesa el cuerpo del else
    parse_statement(tokens[1:], symbol_table)

def determine_type(value):
    if isinstance(value, bool):
        return 'boolean'
    elif isinstance(value, (int, float)):
        return 'number'
    elif isinstance(value, str):
        return 'string'
    else:
        raise SyntaxError(f'Tipo no soportado: {type(value).__name__}')

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

        new_type = determine_type(value)

        if var_name in symbol_table:
            existing_type = types[var_name]
            if existing_type != new_type:
                line_num = tokens[0][2]
                raise SyntaxError(f'Error en línea {line_num}: Variable "{var_name}" es de tipo {existing_type}, no se puede asignar {new_type}')
            # Actualizar valor
            symbol_table[var_name] = value
        else:
            # Crear nueva entrada
            # symbol_table[var_name] = {
            #     'value': new_value,
            #     'type': new_type
            # }
            symbol_table[var_name] = value
            unused_vars[var_name] = {
                'value': value,
                'used': False  # Inicialmente no usada
            }
            types[var_name] = new_type
    else:
        line_num = tokens[0][2] if tokens else '?'
        raise SyntaxError(f'Error de sintaxis en la línea {line_num}.')

def find_unused_variables(symbol_table):
    unused = []
    for var, data in unused_vars.items():
        if var.startswith('__'):  # Ignorar variables internas
            continue
        if isinstance(data, dict) and not data.get('used', False):
            unused.append(var)
    return unused

def get_usage_functions_warnings():
    warnings = []
    
    # Verificar funciones no llamadas
    for func_name, func_data in unused_fns.items():
        if not func_data['called']:
            warnings.append(f'⚠️ Función "{func_name}" declarada pero nunca usada')
            
    return warnings

# Función para evaluar expresiones aritméticas
def evaluate_expression(tokens, symbol_table):
    expr = ""
    for token_type, token_value, line_num in tokens:
        if token_type == 'IDENTIFIER':
            if token_value in symbol_table:
                if token_value in unused_vars:
                    unused_vars[token_value]['used'] = True
                # Si es un string, añadir comillas al valor
                if isinstance(symbol_table[token_value], str):
                    expr += f'"{symbol_table[token_value]}"'
                else:
                    expr += str(symbol_table[token_value])
            else:
                raise SyntaxError(f'Variable no definida en la línea {line_num}: {token_value}')
        elif token_type == 'STRING':
            expr += token_value  # Ya incluye comillas
        elif token_type in ('NUMBER', 'OPERATOR'):
            expr += token_value
        else:
            raise SyntaxError(f'Error de sintaxis en la expresión en la línea {line_num}: {token_value}')
    try:
        result = eval(expr)
    except Exception as e:
        error_str = str(e)
        traduccion = GoogleTranslator(source='en', target='es').translate(error_str)
        raise SyntaxError(f'Error evaluando la expresión: {expr} ({traduccion})')
    return result

@app.route('/compile', methods=['POST'])
def compile_code():
    code = request.json.get('code', '').strip()
    unused_vars = {}
    unused_fns = {}
    types = {}
    logs.clear()
    if not code:
        return jsonify({'error': 'El código no puede estar vacío.'}), 400
    
    try:
        tokens_detected, minified_code = lexer(code)
        symbol_table = parse_program(tokens_detected)
        unused = find_unused_variables(symbol_table)
        unused_fns_local = get_usage_functions_warnings()
        warnings = [f'⚠️ Variable "{var}" declarada pero no usada' for var in unused]

        return jsonify({
            'message': 'Compilado con éxito.',
            'variables': symbol_table,
            'minified_code': minified_code,
            'tokens_found': tokens_detected,
            'logs': logs,
            'warnings': warnings,
            'warnings_fns': unused_fns_local
        })
    
    except SyntaxError as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
