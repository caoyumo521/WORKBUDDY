#!/usr/bin/env python
"""端到端测试新接口"""
import requests

BASE = "http://127.0.0.1:8088"

# 1. 取项目
projects = requests.get(f"{BASE}/api/projects").json()
# 找有图片的项目
PID = None
for p in projects:
    r = requests.get(f"{BASE}/api/projects/{p['id']}/preview-sources")
    if r.status_code == 200:
        d = r.json()
        if sum(len(m["images"]) for m in d["modules"]) > 0:
            PID = p["id"]
            break
if not PID:
    PID = projects[0]["id"]
print(f"Project: {PID}")

# 2. preview-sources
r = requests.get(f"{BASE}/api/projects/{PID}/preview-sources")
print(f"preview-sources status: {r.status_code}")
if r.status_code != 200:
    print(f"  body: {r.text[:300]}")
    print("No images in this project, skip rest")
    exit(0)
d = r.json()
print(f"  modules: {len(d['modules'])}")
for m in d["modules"]:
    print(f"    {m['key']}: {len(m['images'])} imgs")

OUT = "C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/backend/tests/out"

# 3. format conversion
if d["modules"] and d["modules"][0]["images"]:
    asset_url = d["modules"][0]["images"][0]["url"]
    base_url = asset_url.replace("/api/files?", "").replace("path=", "")
    r = requests.get(f"{BASE}/api/files?path={base_url}&format=jpeg")
    print(f"\nJPEG conversion: status={r.status_code} type={r.headers.get('content-type')} size={len(r.content)}")
    with open(f"{OUT}_sample.jpg", "wb") as f:
        f.write(r.content)

    r = requests.get(f"{BASE}/api/files?path={base_url}&format=webp")
    print(f"WEBP conversion: status={r.status_code} type={r.headers.get('content-type')} size={len(r.content)}")
    with open(f"{OUT}_sample.webp", "wb") as f:
        f.write(r.content)

OUT = "C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/backend/tests/out"

# 4. combined preview
r = requests.get(f"{BASE}/api/files/preview/{PID}?format=png")
print(f"\nCombined PNG: status={r.status_code} type={r.headers.get('content-type')} size={len(r.content)}")
with open(f"{OUT}_combined.png", "wb") as f:
    f.write(r.content)

r = requests.get(f"{BASE}/api/files/preview/{PID}?format=jpeg")
print(f"Combined JPEG: status={r.status_code} type={r.headers.get('content-type')} size={len(r.content)}")
with open(f"{OUT}_combined.jpg", "wb") as f:
    f.write(r.content)