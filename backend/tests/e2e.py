import json, sys, time
import urllib.request

BASE = "http://127.0.0.1:8088"

# 列出项目
with urllib.request.urlopen(f"{BASE}/api/projects") as r:
    projects = json.loads(r.read())
pid = projects[0]["id"]
print("Project:", pid)

# 跑生图
req = urllib.request.Request(
    f"{BASE}/api/generation/project/{pid}/run",
    data=b"{}",
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as r:
    print("Run:", r.read().decode())

# 等待并查看任务
time.sleep(8)
with urllib.request.urlopen(f"{BASE}/api/generation/project/{pid}/tasks") as r:
    tasks = json.loads(r.read())
for t in tasks:
    print(f"  task#{t['id']} {t['module_key']:15s} {t['status']:8s} {t['progress']:3d}% | {(t['message'] or '')[:60]}")

# 资产
with urllib.request.urlopen(f"{BASE}/api/generation/project/{pid}/assets") as r:
    assets = json.loads(r.read())
print(f"\n=== {len(assets)} assets ===")
for a in assets:
    if a["status"] == "success":
        print(f"  #{a['id']} {a['asset_type']:12s} {a['module_key']:15s} -> {a['file_path']}")

# 导出 HTML
req = urllib.request.Request(
    f"{BASE}/api/export/project/{pid}?format=html",
    data=b"",
    method="POST",
)
with urllib.request.urlopen(req) as r:
    out_path = r.read().decode()
    print("\nExported HTML ->", out_path)
