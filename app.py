from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from privacy_ai import sanitize_with_ollama

app = Flask(__name__)

# Configure CORS specifically for Chrome extensions
CORS(app, origins=[
    "chrome-extension://*",
    "moz-extension://*", 
    "http://localhost:*",
    "http://127.0.0.1:*"
], supports_credentials=True)

@app.route('/')
def health_check():
    return jsonify("Hi it is working perfectly")

@app.route('/sanitize', methods=['POST', 'OPTIONS'])
def sanitize():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    data = request.json
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
        
    user_input = data.get('text', '')
    if not user_input:
        return jsonify({'error': 'No text provided'}), 400
        
    try:
        sanitized_text = sanitize_with_ollama(user_input)
        #print(sanitized_text, type(sanitized_text))
        
        response = jsonify({
            'Masked': sanitized_text.get('Masked', ''),
            'Rephrased': sanitized_text.get('Rephrased', ''),
            'Synthetic': sanitized_text.get('Synthetic', '')
        })
        
        # Add CORS headers manually as backup
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        
        return response
        
    except Exception as e:
        error_response = jsonify({'error': str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
