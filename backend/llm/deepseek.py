import os, requests
from typing import List, Dict

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

def _headers():
    return {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}

def embed_text(text: str) -> List[float]:
    url = f"{BASE_URL}/v1/embeddings"
    payload = {"model": "deepseek-embedding", "input": text}
    resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]

def chat(messages: List[Dict], stream: bool=False) -> str:
    url = f"{BASE_URL}/chat/completions"
    payload = {"model": "deepseek-chat", "messages": messages, "stream": stream}
    resp = requests.post(url, headers=_headers(), json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]