from flask import Flask, request, jsonify
from flask_cors import CORS
from lexer import lexer
from parser import parse_program
from config import logs 

app = Flask(__name__)
CORS(app)

@app.route('/compile', methods=['POST'])
def compile_code():
    code = request.json.get('code', '').strip()
    logs.clear()
    if not code:
        return jsonify({'error': 'El código no puede estar vacío.'}), 400
    
    try:
        tokens_detected, minified_code = lexer(code)
        symbol_table = parse_program(tokens_detected)

        return jsonify({
            'message': 'Compilado con éxito.',
            'variables': symbol_table,
            'minified_code': minified_code,
            'tokens_found': tokens_detected,
            'logs': logs
        })
    
    except SyntaxError as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
