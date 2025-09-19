import subprocess
import requests
import time
import atexit
import os
import signal
import ollama
from src.prompt_detailed import prompt_str
import json
import re

OLLAMA_URL = "http://localhost:11434"
#OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_MODEL = "gemma2:2b"
OLLAMA_PROCESS = None  # global reference to the server process

def start_ollama_server():
    """Start Ollama server safely in a new process group."""
    global OLLAMA_PROCESS
    #print("Starting Ollama server...")
    
    creationflags = 0
    preexec_fn = None
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        preexec_fn = os.setsid

    OLLAMA_PROCESS = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=preexec_fn,
        creationflags=creationflags
    )

    # Ensure process is terminated on script exit
    atexit.register(stop_ollama_server)

    # Wait for server to become available
    for i in range(20): 
        try:
            requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            #print("Ollama server is ready.")
            return
        except requests.ConnectionError:
            print(f"Waiting for Ollama server... ({i+1}/20)")
            time.sleep(1)

    stop_ollama_server()
    raise RuntimeError("Failed to start Ollama server.")

def stop_ollama_server():
    """Terminate Ollama server and all child processes."""
    global OLLAMA_PROCESS
    if OLLAMA_PROCESS is None:
        return

    #print("Stopping Ollama server...")
    try:
        if os.name == "nt":
            # Windows: terminate the process and its children
            OLLAMA_PROCESS.send_signal(signal.CTRL_BREAK_EVENT)
            OLLAMA_PROCESS.kill()
        else:
            # Unix/macOS: kill the process group
            os.killpg(os.getpgid(OLLAMA_PROCESS.pid), signal.SIGTERM)
    except Exception as e:
        print("Error stopping Ollama server:", e)
    finally:
        OLLAMA_PROCESS = None

def ensure_ollama_running():
    """Check if Ollama server is running, start it if not."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        #print("Ollama server already running.")
        #print(f"Available models: {response.json()}")
        return True
    except requests.ConnectionError:
        print("Ollama server not running, attempting to start...")
        try:
            start_ollama_server()
            return True
        except Exception as e:
            print(f"Failed to start Ollama server: {e}")
            return False
    except Exception as e:
        print(f"Error checking Ollama server: {e}")
        return False

def clean_json_text(text):
    """Clean up text to extract valid JSON"""
    # Remove markdown code blocks
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) > 1:
            text = "\n".join(lines[1:])
    if text.endswith("```"):
        lines = text.splitlines()
        if len(lines) > 0:
            text = "\n".join(lines[:-1])
    
    text = text.strip()
    
    # Try to find JSON object in the text
    # Look for { ... } pattern
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    # If no JSON object found, return the cleaned text
    return text

def sanitize_with_ollama(user_input):
    """Send user input to Ollama for processing using the Python library."""
    #print(f"Starting sanitization for: {user_input[:50]}...")
    
    # Ensure Ollama is running before making requests
    if not ensure_ollama_running():
        raise RuntimeError("Ollama server is not available")
    
    prompt = f"{prompt_str}\n\nUser input: {user_input}\n\nSanitized output:"
    #print(f"Prompt length: {len(prompt)} characters")
    
    try:
        #print(f"Calling ollama.generate with model: {OLLAMA_MODEL}")
        # Using ollama.generate instead of manual requests
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        #print(f"Ollama response type: {type(response)}{response}")
        # start = response.find("{")
        # end = response.rfind("}") + 1
        # text = response[start:end]
        #Extract text from response
        if isinstance(response, str):
            # Find the first '{' and the last '}'
            start = response.find("{")
            end = response.rfind("}") + 1
            text = response[start:end]
            # text = response.strip("`")       # removes leading/trailing backticks
            # text = text.replace("json\n", "") # remove the 'json' language tag 
            text = text.strip()
        elif hasattr(response, "response"):
            start = response.response.find("{")
            end = response.response.rfind("}") + 1
            text = response.response[start:end]
            # text = response.response.strip("`")
            # text = text.replace("json\n", "") # remove the 'json' language tag 
            text = text.strip()
        else:
            start = str(response).find("{")
            end = str(response).rfind("}") + 1
            text = response[start:end]
            # text = str(response).strip("`")
            # text = text.replace("json\n", "") # remove the 'json' language tag 
            text = text.strip()
        
        print(f"Extracted text length: {len(text)}")
        print(f"Raw response: {text[:200]}...")
        
    except Exception as e:
        print(start, end)
        print(f"Error in ollama.generate: {e}")
        raise RuntimeError(f"Failed to generate from Ollama model: {e}")

    # Clean the text to extract JSON
    #cleaned_text = clean_json_text(text)
    cleaned_text = text
    print(f"Cleaned text: {cleaned_text[:200]}...", type(cleaned_text))
    
    try:
        parsed = json.loads(cleaned_text)
        print(f"Successfully parsed JSON: {parsed}")
        
        if isinstance(parsed, dict):
            # Ensure the expected keys exist, fallback if missing
            result = {
                'Masked': parsed.get('Masked', ''),
                'Rephrased': parsed.get('Rephrased', ''),
                'Synthetic': parsed.get('Synthetic', '')
            }
            #print(f"Returning result: {result}")
            return result
        else:
            # If JSON is not a dict, return the raw string
            result = {'Masked': cleaned_text, 'Rephrased': cleaned_text, 'Synthetic': cleaned_text}
            print(f"Non-dict JSON, returning: {result}")
            return result
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Text that failed to parse: {cleaned_text}")
        
        # try:
        #     parsed = json.dumps(cleaned_text)
        #     print(f"Successfully parsed JSON using DUMPS!!!!: {parsed}")
            
        #     if isinstance(parsed, dict):
        #         # Ensure the expected keys exist, fallback if missing
        #         result = {
        #             'Masked': parsed.get('Masked', ''),
        #             'Rephrased': parsed.get('Rephrased', ''),
        #             'Synthetic': parsed.get('Synthetic', '')
        #         }
        #         #print(f"Returning result: {result}")
        #         return result
        #     else:
        #         # If JSON is not a dict, return the raw string
        #         result = {'Masked': cleaned_text, 'Rephrased': cleaned_text, 'Synthetic': cleaned_text}
        #         print(f"Non-dict JSON, returning: {result}")
        #         return result
        # except json.JSONDecodeError as e:
        #     print(f"JSON decode error: {e}")
        #     print(f"Text that failed to parse: {cleaned_text}")

        # Try to extract individual fields using regex as last resort
        try:
            masked_match = re.search(r'"Masked":\s*"([^"]*(?:\\.[^"]*)*)"', cleaned_text)
            rephrased_match = re.search(r'"Rephrased":\s*"([^"]*(?:\\.[^"]*)*)"', cleaned_text)
            synthetic_match = re.search(r'"Synthetic":\s*"([^"]*(?:\\.[^"]*)*)"', cleaned_text)
            
            result = {
                'Masked': masked_match.group(1) if masked_match else cleaned_text,
                'Rephrased': rephrased_match.group(1) if rephrased_match else cleaned_text,
                'Synthetic': synthetic_match.group(1) if synthetic_match else cleaned_text
            }
            print(f"Regex extraction result: {result}")
            return result
        except Exception as regex_error:
            print(f"Regex extraction failed: {regex_error}")
            # Final fallback: return the cleaned text in all fields
            result = {'Masked': cleaned_text, 'Rephrased': cleaned_text, 'Synthetic': cleaned_text}
            print(f"Final fallback result: {result}")
            return result


if __name__ == "__main__":
    ensure_ollama_running()
    user_input = input("Enter your prompt: ")
    sanitized = sanitize_with_ollama(user_input)
    print("Sanitized output:\n", sanitized)
    # Stop Ollama server safely
    #stop_ollama_server()
