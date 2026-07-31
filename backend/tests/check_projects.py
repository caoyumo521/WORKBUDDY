#!/usr/bin/env python
import requests

BASE = "http://127.0.0.1:8088"
projects = requests.get(f"{BASE}/api/projects").json()
for p in projects:
    r = requests.get(f"{BASE}/api/projects/{p['id']}/preview-sources")
    img_count = 0
    if r.status_code == 200:
        d = r.json()
        img_count = sum(len(m["images"]) for m in d["modules"])
    print(f"{p['id'][:30]} - {p['name'][:30]}: {r.status_code} imgs={img_count}")
    if r.status_code != 200:
        print(f"  body: {r.text[:200]}")