# AI 电商详情页生产工作台

> 本地优先 / 模块化架构 / 可平滑迁移到云服务器的「AI 电商详情页自动生产工作台」。  
> 对标 51aic、yilaitu 的详情页生成平台。



![](local-file:///C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/docs/screenshots/01_projects.png)

## 核心特性

- 🎨 **6 步可视化向导**：产品图 → 行业/平台 → 详情图要求 → 视觉/语言/尺寸 → 详情图模块 → 创建
- 🧩 **模块化详情页**：19+ 通用模块 + 14 个行业预设，自由组合 / AI 自动规划
- 🖼 **统一生图接口**：通过 `.env` 一键切换 OpenAI / Flux / 自有 API / Mock
- 📁 **资产真实落盘**：每个项目独立目录，图片按模块归档，可断点续传
- 📦 **一键导出 Word / PDF / HTML**：审核、团队协作、独立站部署全场景
- 🔌 **可平滑迁移**：本地 SQLite + 本地文件存储；Docker / OSS / S3 后续无缝切换

## 快速开始

### Windows

```bash
双击 start.bat
```

### macOS / Linux

```bash
bash start.sh
```

启动脚本会自动：

1. 创建 Python 虚拟环境并安装依赖
2. 安装前端依赖（首次）
3. 启动后端（端口 8088）
4. 启动前端（端口 5173）
5. 自动打开浏览器

## 手动启动

```bash
# 后端
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
cp .env.example .env
python run.py

# 前端（新开终端）
cd frontend
npm install
npm run dev
```

访问 <http://127.0.0.1:5173/>

## 配置生图 API

编辑 `backend/.env`：

```ini
# 选择 provider：openai | flux | custom | mock
IMAGE_PROVIDER=custom

# 自有 API
IMAGE_BASE_URL=https://your-image-api.example.com/v1
IMAGE_API_KEY=sk-xxxxxx
IMAGE_MODEL=your-model-name
```

各 provider 请求约定见 `backend/app/services/image_providers/`：

- **mock** - 无 API 时本地占位（生成渐变图，验证整条链路）
- **openai** - 兼容 DALL·E 3 / gpt-image-1
- **flux** - BFL Flux Pro
- **custom** - 你自己的内部 API，按以下 JSON 协议即可对接

```json
POST {IMAGE_BASE_URL}/images/generations
{
  "model": "...",
  "prompt": "...",
  "width": 1024,
  "height": 1024,
  "reference_images": ["data:image/png;base64,..."]
}
→ { "data": [{ "url": "...", "width": 1024, "height": 1024 }] }
```

## 目录结构

```
detail-page-studio/
├── backend/                      # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 统一配置（.env）
│   │   ├── database.py          # SQLAlchemy
│   │   ├── models/              # 数据模型
│   │   ├── schemas/             # Pydantic
│   │   ├── routers/             # API 路由
│   │   ├── services/            # 业务服务
│   │   │   ├── image_service.py            # 抽象接口
│   │   │   ├── image_providers/            # 多 provider 实现
│   │   │   ├── ai_service.py               # 详情页规划 LLM
│   │   │   ├── project_service.py
│   │   │   └── document_service.py         # Word/PDF/HTML 导出
│   │   └── utils/               # 文件管理 / Prompt 模板
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   └── run.py
├── frontend/                     # Vite + React + TS
│   ├── src/
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── ProjectsPage.tsx
│   │   │   ├── NewProjectPage.tsx   # 6 步创建向导
│   │   │   └── ProjectDetailPage.tsx
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── SelectGrid.tsx
│   │   └── lib/api.ts
│   ├── package.json
│   └── vite.config.ts
├── projects/                     # 项目数据（运行时生成）
│   └── proj_20260730_xxx_名字/
│       ├── project.json
│       ├── 01_产品资料/
│       ├── 02_参考案例/
│       ├── 03_视觉分析/
│       ├── 04_页面策划/
│       ├── 05_Prompts/
│       ├── 06_生成图片/
│       │   ├── 01_Hero首屏/
│       │   ├── 04_CoreSelling核心卖点/
│       │   └── ...
│       ├── 07_文案/
│       ├── 08_文档/
│       └── 09_导出/
├── docs/
│   └── screenshots/              # UI 截图
├── start.bat                     # Windows 一键启动
├── start.sh                      # macOS / Linux 一键启动
├── docker-compose.yml            # 服务端部署
├── nginx.conf
└── README.md
```

## API 总览

| 路径                                                     | 用途                  |
| ------------------------------------------------------ | ------------------- |
| `GET  /api/health`                                     | 健康检查                |
| `GET  /api/projects`                                   | 项目列表                |
| `POST /api/projects/from-wizard`                       | 从向导创建项目（带 AI 规划）    |
| `GET  /api/projects/{id}`                              | 项目详情                |
| `PATCH /api/projects/{id}`                             | 更新项目                |
| `DELETE /api/projects/{id}`                            | 删除项目（含磁盘）           |
| `POST /api/upload/project/{id}`                        | 上传产品图/参考图           |
| `POST /api/generation/project/{id}/run`                | 启动生图任务              |
| `GET  /api/generation/project/{id}/tasks`              | 任务列表                |
| `POST /api/generation/task/{id}/retry`                 | 失败重试                |
| `GET  /api/generation/project/{id}/assets`             | 资产列表                |
| `POST /api/export/project/{id}?format=html\|docx\|pdf` | 导出                  |
| `GET  /api/meta/...`                                   | 静态字典：行业/平台/语言/比例/模块 |
| `POST /api/ai/help`                                    | AI 帮写详情图要求          |

完整文档：<http://127.0.0.1:8088/docs>

## 开发路线

按你的项目原则，本仓库严格按以下顺序迭代：

- [x] **第一阶段**：项目创建、产品信息、行业/平台/语言/风格/分辨率
- [x] **第二阶段**：AI 分析、详情页结构、模块化页面规划、Prompt 生成
- [x] **第三阶段**：生图 API 接入、图片生成、保存、分类、预览、重生成
- [x] **第四阶段**：Word / PDF / HTML 详情页自动组合与导出
- [ ] **第五阶段**：历史项目、模板管理、参考案例管理、视觉风格库
- [ ] 长期：竞品分析、Shopify 一键发布、A/B 版本、广告素材、社媒素材

## 未来服务器部署

```bash
# 后端打包
cd backend && docker build -t dps-backend .

# 前端打包
cd frontend && npm run build

# 一键起服
cd .. && docker compose up -d
```

- 后端：`http://server:8088/`
- 前端：`http://server:5173/`
- 切换到 PostgreSQL：改 `backend/.env` 的 `DATABASE_URL`
- 切换到 OSS / S3：在 `services/image_service.py` 中实现 storage 抽象

## 截图

### 项目列表

![](local-file:///C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/docs/screenshots/01_projects.png)

### 创建向导 - 步骤 1 产品信息

![](local-file:///C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/docs/screenshots/02_wizard.png)

### 创建向导 - 步骤 2 行业/平台

![](local-file:///C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/docs/screenshots/wizard_step1.png)

### 创建向导 - 步骤 4 视觉/语言/尺寸

![](local-file:///C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/docs/screenshots/wizard_step3.png)

### 创建向导 - 步骤 5 详情图模块

![](local-file:///C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/docs/screenshots/wizard_step4.png)

### 项目工作台

![](local-file:///C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/docs/screenshots/03_detail.png)

### 导出 HTML 详情页

![](local-file:///C:/Users/EDY/WorkBuddy/2026-07-30-14-59-19/detail-page-studio/docs/screenshots/04_exported_html.png)

## License

Private
