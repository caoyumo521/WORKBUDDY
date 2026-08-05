"""端到端验证：创建项目 → 生成 hero → 检查成品图带文案。"""
import json
import time
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8091"


def req(method: str, path: str, data: dict | None = None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data, ensure_ascii=False).encode("utf-8") if data else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


# 1) 创建项目
project = req(
    "POST",
    "/api/projects/from-wizard",
    {
        "name": "E2E-TextOverlay-测试",
        "industry": "apparel",
        "target_market": "中国",
        "target_platform": "淘宝",
        "language": "zh-CN",
        "visual_style": "fresh",
        "resolution": "1K",
        "aspect_ratio": "3:4",
        "product_name": "云感透气运动T恤",
        "product_selling_points": "冰丝面料、速干透气、修身显瘦",
        "product_target_audience": "18-35岁都市白领",
        "product_description": "专为夏季运动设计的轻薄T恤",
        "module_keys": ["hero"],
        "module_quantities": {"hero": 1},
    },
)
print("created project", project["id"])

# 2) 触发生成
run = req(
    "POST",
    f"/api/generation/project/{project['id']}/run",
    {"module_keys": ["hero"]},
)
print("queued", run["queued"], "tasks", run["task_ids"])

# 3) 轮询任务
for _ in range(60):
    time.sleep(2)
    tasks = req("GET", f"/api/generation/project/{project['id']}/tasks")
    task = next((t for t in tasks if t["id"] == run["task_ids"][0]), None)
    if not task:
        continue
    print("task", task["id"], task["status"], task["progress"], task.get("message", ""))
    if task["status"] in ("success", "failed"):
        break

# 4) 检查资产
assets = req("GET", f"/api/generation/project/{project['id']}/assets")
print("assets:", [(a["asset_type"], a["module_key"], a["seq"], a["file_path"]) for a in assets])

composed = [a for a in assets if a["asset_type"] == "composed"]
assert composed, "未生成 composed 成品图"
print("composed path:", composed[0]["file_path"])

# 5) 检查文件存在且非空
p = Path(composed[0]["file_path"])
assert p.exists(), f"成品图不存在: {p}"
assert p.stat().st_size > 1000, f"成品图太小: {p.stat().st_size}"
print("OK: end-to-end text overlay verified")
