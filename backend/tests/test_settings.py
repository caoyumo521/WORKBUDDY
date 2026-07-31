#!/usr/bin/env python
import requests
import json

BASE = "http://127.0.0.1:8088"

print("=== Settings PUT ===")
r = requests.put(f"{BASE}/api/settings", json={
    "image": {
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-image-1",
        "api_key": "sk-test12345678",
        "quality": "high",
        "output_format": "jpeg"
    },
    "text": {
        "provider": "openai",
        "model": "gpt-4o",
        "api_key": "sk-text1234"
    }
})
d = r.json()
print(f"image: {d['image']['provider']} / {d['image']['model']} mask={d['image']['api_key_masked']} has={d['image']['has_api_key']}")
print(f"text:  {d['text']['provider']} / {d['text']['model']} mask={d['text']['api_key_masked']}")

print("\n=== Settings GET ===")
r = requests.get(f"{BASE}/api/settings")
d = r.json()
print(f"image provider: {d['image']['provider']}, model: {d['image']['model']}")
print(f"text model: {d['text']['model']}, masked: {d['text']['api_key_masked']}")

print("\n=== Test text connection (fake key, expect fail) ===")
r = requests.post(f"{BASE}/api/settings/test/text")
print(json.dumps(r.json(), indent=2, ensure_ascii=False))

print("\n=== KEEP api_key ===")
r = requests.put(f"{BASE}/api/settings", json={
    "text": {"api_key": "__KEEP__", "model": "gpt-4o-mini"}
})
d = r.json()
print(f"text api_key still masked: {d['text']['api_key_masked']} (should be unchanged)")

print("\n=== CLEAR api_key ===")
r = requests.put(f"{BASE}/api/settings", json={
    "text": {"api_key": "__CLEAR__"}
})
d = r.json()
print(f"text api_key after clear: masked='{d['text']['api_key_masked']}' has={d['text']['has_api_key']}")