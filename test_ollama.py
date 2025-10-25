import requests
import sys
sys.stdout.reconfigure(line_buffering=True)

BASE = "https://think-turner-lang-specifics.trycloudflare.com" # no trailing slash
print("Pinging tags…")
ping = requests.get(f"{BASE}/api/tags", timeout=15)
print(ping.status_code, ping.text)

print("Generating…")
r = requests.post(
f"{BASE}/api/generate",
json={"model": "llama3:latest", "prompt": "Hello from Codespaces", "stream": False},
timeout=120,
)
print(r.status_code, r.text)

