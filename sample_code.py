import requests
import json

# URL of your local LLM API server
url = "http://localhost:11434/api/generate"

# Define your prompt (stream: True is the default, but we can be explicit)
payload = {
    "model": "mario",
    "prompt": "Write a short poem about the ocean at sunset.",
    "stream": True 
}

# Send POST request
# We add stream=True to the request itself to tell the 'requests'
# library to handle this as a streaming connection.
try:
    response = requests.post(url, json=payload, stream=True)
    response.raise_for_status()

    print("Model response (streaming):")
    
    # Iterate over the response line by line
    for line in response.iter_lines():
        if line:
            try:
                # Each line is a new JSON object
                data = json.loads(line)
                
                # We print the 'response' key from this JSON object
                # end='' prevents a new line after each token
                # flush=True ensures it prints to the console immediately
                print(data['response'], end='', flush=True)

            except json.JSONDecodeError:
                print(f"\nError decoding JSON: {line}")
    
    print() # Add a final newline after the stream is done

except requests.exceptions.ConnectionError:
    print(f"Error: Could not connect to the server at {url}.")
    print("Please make sure your local Ollama server is running.")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
