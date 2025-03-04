# Función para evaluar expresiones aritméticas
def evaluate_expression(tokens, symbol_table):
    expr = ""
    for token_type, token_value, line_num in tokens:
        if token_type == 'IDENTIFIER':
            if token_value in symbol_table:
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
        raise SyntaxError(f'Error evaluando la expresión: {expr} ({e})')
    return result