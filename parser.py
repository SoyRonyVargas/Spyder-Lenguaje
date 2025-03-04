from evaluator import evaluate_expression
from config import logs 

def parse_program(tokens):
    if tokens[0][0] != 'START' or tokens[-1][0] != 'END':
        raise SyntaxError('El programa debe comenzar con "INICIO" y terminar con "FIN".')
    
    in_program = False
    symbol_table = {}
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
    elif tokens[0][1] == '{':
        parse_block(tokens, symbol_table)
    else:
        parse_assignment(tokens, symbol_table)

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
        raise SyntaxError(f'Error de sintaxis en la línea {line_num}.')
