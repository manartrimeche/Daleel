import urllib.request
import json
import time

url = 'http://127.0.0.1:8000/api/v1/ask'
data = {
    'question': 'Quelles sont les obligations du gerant?',
    'top_k': 3,
    'temperature': 0.1,
    'history': []
}
params = json.dumps(data).encode('utf8')
req = urllib.request.Request(url, data=params, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req, timeout=180) as response:
        res_body = response.read().decode('utf8')
        res_json = json.loads(res_body)
        print(f"STATUS: {response.getcode()}")
        print(f"MODEL: {res_json.get('model', 'N/A')}")
        print(f"CHUNKS: {len(res_json.get('chunks_used', []))}")
        answer = res_json.get('answer', '')
        first_line = answer.split('\n')[0] if answer else 'No answer'
        print(f"ANSWER: {first_line}")
except Exception as e:
    print(f"ERROR: {str(e)}")
