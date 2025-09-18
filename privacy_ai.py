import subprocess
import requests
import time
import atexit
import os
import signal
import ollama
from src.prompt import prompt_str
import json

OLLAMA_URL = "http://localhost:11434"
#OLLAMA_MODEL = "mistral:7b-instruct"
OLLAMA_MODEL = "gemma2:2b"
OLLAMA_PROCESS = None  # global reference to the server process

def start_ollama_server():
    """Start Ollama server safely in a new process group."""
    global OLLAMA_PROCESS
    print("Starting Ollama server...")
    
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
    for i in range(0.1):  # wait up to 20 seconds
        try:
            requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            print("Ollama server is ready.")
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

    print("Stopping Ollama server...")
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
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        print("Ollama server already running.")
    except requests.ConnectionError:
        print("STARTING OVER OLLAMA SERVER !!!! !!!!")
        start_ollama_server()

def sanitize_with_ollama(user_input):
    """Send user input to Ollama for processing using the Python library."""
    #system_prompt = "You are a helpful AI assistant."
    prompt = f"{prompt_str}\n\nUser input: {user_input}\n\nSanitized output:"
    
    try:
        # Using ollama.generate instead of manual requests
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=prompt
        )
        # If response is already a string, just strip whitespace
        if isinstance(response, str):
            text = response.strip()
        # If response is a dict/object, adjust accordingly
        elif hasattr(response, "response"):
            text = response.response.strip()
        else:
            # fallback: convert to string
            text = str(response).strip()
        # Clean up markdown fences if present
        text = text.strip()
        if text.startswith("```"):
            # remove first line (```json or ```)
            text = "\n".join(text.splitlines()[1:])
        if text.endswith("```"):
            # remove last line ```
            text = "\n".join(text.splitlines()[:-1])
    except Exception as e:
        raise RuntimeError(f"Failed to generate from Ollama model: {e}")

    # print(text, type(text))
    # print("____________")
    # print(json.loads(text), "####")
    
    try:
        parsed = json.loads(text)
        # print(parsed, "****")
        if isinstance(parsed, dict):
            # Ensure the expected keys exist, fallback if missing
            return {
                'Masked': parsed.get('Masked', ''),
                'Rephrased': parsed.get('Rephrased', ''),
                'Synthetic': parsed.get('Synthetic', '')
            }
        else:
            # If JSON is not a dict, return the raw string
            return text
    except json.JSONDecodeError:
        # Not valid JSON, return raw string
        return text


if __name__ == "__main__":
    ensure_ollama_running()
    user_input = input("Enter your prompt: ")
    sanitized = sanitize_with_ollama(user_input)
    print("Sanitized output:\n", sanitized)
    # Stop Ollama server safely
    #stop_ollama_server()
