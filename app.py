from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
from privacy_ai import sanitize_with_ollama
import traceback
import threading
import time

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

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint to verify server is working"""
    return jsonify({
        'status': 'ok',
        'message': 'Flask server is working',
        'ollama_available': check_ollama_availability()
    })

def check_ollama_availability():
    """Check if Ollama is available without starting it"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return True
    except:
        return False

def run_with_timeout(func, timeout_seconds):
    """Run a function with a timeout using threading"""
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        # Thread is still running, timeout occurred
        raise TimeoutError(f"Function timed out after {timeout_seconds} seconds")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

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
    
    print(f"Processing request for text: {user_input[:100]}...")
        
    try:
        print("Calling sanitize_with_ollama...")
        
        # Use threading-based timeout instead of signal
        sanitized_text = run_with_timeout(
            lambda: sanitize_with_ollama(user_input),
            50  # 50 second timeout
        )
        
        print(f"Got response: {sanitized_text}")
        
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
        
    except TimeoutError as e:
        print(f"Timeout error: {e}")
        error_response = jsonify({'error': f'AI processing timeout: {str(e)}'})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 408  # Request Timeout
    except Exception as e:
        print(f"Error in sanitize endpoint: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        error_response = jsonify({'error': str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        return error_response, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
