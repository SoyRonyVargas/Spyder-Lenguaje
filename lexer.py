import re

tokens = [
    ('START', r'\bINICIO\b'),
    ('END', r'\bFIN\b'),
    ('KEYWORD', r'\b(if|else|print|scan|while|doFor)\b'),
    ('OPERATOR', r'(\+|\-|\*|\/|==|<=|>=|=|%|<|>|&|\|)'),
    ('IDENTIFIER', r'\b[A-Za-z_][A-Za-z0-9_]*\b'),
    ('NUMBER', r'\b\d+(\.\d+)?\b'),
    ('STRING', r'\".*?\"'),
    ('SYMBOL', r'[!()\{\};]'),
    ('COMMENT', r'#.*'),
    ('WHITESPACE', r'\s+'),
    ('NEWLINE', r'!'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('SYMBOL', r'[!()]'),
]

def lexer(code):
    pos = 0
    line_num = 1
    tokens_found = []
    minified_code = ""
    
    while pos < len(code):
        match = None
        for token_type, token_regex in tokens:
            pattern = re.compile(token_regex)
            match = pattern.match(code, pos)
            if match:
                token_value = match.group(0)
                if token_type not in ['WHITESPACE', 'COMMENT']:
                    tokens_found.append((token_type, token_value, line_num))
                    minified_code += token_value
                if token_type == 'NEWLINE':
                    line_num += 1
                pos = match.end(0)
                line_num += token_value.count('!')
                break
        if not match:
            raise SyntaxError(f'Error léxico en la línea {line_num}, posición {pos}: "{code[pos]}"')
    return tokens_found, minified_code