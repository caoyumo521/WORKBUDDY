# AI 详情页生产工作台 V1 PRD

> **版本**: V1.0 | **日期**: 2026-07-30 | **状态**: MVP 已跑通，进入迭代阶段

---

## 一、产品定位

### 核心流程

```
产品输入 → AI分析 → 详情页结构生成 → Prompt生成 → 图片API调用 → 图片自动保存 → 自动生成文档
```

### V1 目标

> 30 分钟生成一个专业详情页初稿，人工只需修改 20%。

不做：
- ❌ 训练模型
- ❌ 一键生成完美详情页
- ❌ 复杂 SaaS 多租户

做：
- ✅ 详情页结构自动生成
- ✅ Prompt 自动生成
- ✅ 批量调用生图 API
- ✅ 图片自动归档
- ✅ 自动生成 Word/PDF/HTML 文档

---

## 二、当前 MVP 状态

### 已完成

| 模块 | 状态 | 说明 |
|------|------|------|
| 项目创建 | ✅ | 6 步向导（产品图→行业→平台→AI帮写→语言/风格/比例→模块选择）|
| 产品信息录入 | ✅ | 名称/卖点/用户/描述/附加要求 |
| 行业/品类选择 | ✅ | 14 大行业预设 |
| 目标市场选择 | ✅ | 12 大平台 |
| 语言选择 | ✅ | 13 种语言 |
| 视觉风格选择 | ✅ | 10 种风格 |
| 图片分辨率 | ✅ | 1K/2K/4K |
| AI 分析（模板模式） | ✅ | 行业默认模板回退 |
| 详情页结构生成 | ✅ | 模块化拆解 |
| Prompt 生成 | ✅ | 通用模板 + 知识库模板 |
| 生图 API 调用 | ✅ | mock provider 已验证全链路 |
| 图片自动保存 | ✅ | 按项目/模块分类落盘 |
| 图片管理 | ✅ | 预览/重生成/删除 |
| Word 导出 | ✅ | python-docx，含内嵌图 |
| HTML 导出 | ✅ | 独立可部署页面 |
| 知识库 | ✅ | 4 个行业策略 + 1 个参考案例 |
| Docker 部署 | ✅ | Dockerfile + docker-compose |

### 待接入（需你提供 API Key）

| 模块 | 当前状态 | 接入方式 |
|------|----------|----------|
| GPT Image API 生图 | mock 占位 | `.env` 配置 OpenAI Key |
| AI 思考/文案 | 模板回退 | `.env` 配置 LLM Key 或用 WorkBuddy 预生成策略 |
| PDF 导出 | 未实现 | weasyprint 或 playwright |

---

## 三、技术架构

```
detail-page-studio/
├── backend/                    # Python FastAPI 后端
│   ├── app/
│   │   ├── config.py          # 统一配置中心（.env 读取）
│   │   ├── database.py        # SQLite 连接
│   │   ├── models/            # 数据模型（Project, Asset, GenerationTask）
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── routers/          # API 路由
│   │   │   ├── projects.py   #   项目 CRUD + 向导创建
│   │   │   ├── generation.py #   生图任务管理
│   │   │   ├── upload.py     #   文件上传
│   │   │   ├── files.py      #   文件读取/预览
│   │   │   ├── export.py     #   文档导出
│   │   │   ├── ai.py         #   AI 规划/帮写
│   │   │   └── meta.py       #   元数据（行业/平台/语言）
│   │   ├── services/
│   │   │   ├── image_service.py        # 生图抽象接口 + 工厂
│   │   │   ├── image_providers/       # 各生图后端
│   │   │   │   ├── openai_provider.py  # GPT Image API + DALL·E 3
│   │   │   │   ├── flux_provider.py    # Flux API
│   │   │   │   ├── custom_provider.py  # 自有 API
│   │   │   │   └── mock_provider.py    # 本地占位
│   │   │   ├── ai_service.py           # AI 文本服务（规划/文案/Prompt）
│   │   │   ├── project_service.py      # 项目业务逻辑
│   │   │   └── document_service.py     # Word/HTML 导出
│   │   └── utils/
│   │       ├── file_manager.py  # 文件归档管理
│   │       └── prompts.py       # 模块/行业/风格 元数据 + Prompt 模板
│   ├── .env                   # 配置文件（不提交 Git）
│   └── run.py                 # 启动入口
│
├── frontend/                  # Vite + React + TailwindCSS
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ProjectsPage.tsx       # 项目列表
│   │   │   ├── NewProjectPage.tsx     # 6 步创建向导
│   │   │   └── ProjectDetailPage.tsx  # 项目工作台
│   │   ├── components/
│   │   │   ├── Layout.tsx / Sidebar.tsx
│   │   │   └── SelectGrid.tsx         # 通用选择网格
│   │   └── lib/api.ts                 # API 封装
│   └── vite.config.ts         # 含 /api 代理到 8088
│
├── knowledge/                 # 知识库（AI 的"大脑"）
│   ├── apparel/strategy.json  # 服装行业策略
│   ├── 3c/strategy.json       # 3C 电子行业策略
│   ├── home/strategy.json     # 家居行业策略
│   ├── pet/strategy.json      # 宠物行业策略
│   └── apparel/lululemon/     # 参考案例
│       └── analysis.json
│
├── projects/                  # 生成的项目文件（运行时创建）
│   └── proj_xxx/
│       ├── 01_产品资料/
│       ├── 05_prompts/
│       ├── 06_生成图片/
│       │   ├── 01_hero/
│       │   ├── 02_core_selling/
│       │   └── ...
│       └── 07_文档/
│
├── start.bat / start.sh       # 一键启动
├── docker-compose.yml         # Docker 部署
└── README.md
```

### 技术选型

| 层 | 技术 | 原因 |
|----|------|------|
| 后端 | Python FastAPI | AI 生态最好，异步支持好 |
| 前端 | Vite + React + TailwindCSS | 启动快，依赖轻 |
| 数据库 | SQLite | 零配置，未来可升级 PostgreSQL |
| 文件存储 | 本地文件系统 | 未来可迁移 OSS/S3 |
| 生图 | GPT Image API (gpt-image-1) | 支持参考图编辑，质量最高 |
| 文本 AI | OpenAI 兼容 API | 灵活切换 GPT/Claude/Gemini |
| 部署 | Windows 本地 → Docker | 平滑迁移 |

---

## 四、GPT Image API 对接指南

### 4.1 配置

编辑 `backend/.env`：

```ini
IMAGE_PROVIDER=openai
IMAGE_API_KEY=sk-你的OpenAI密钥
IMAGE_BASE_URL=https://api.openai.com/v1
IMAGE_MODEL=gpt-image-1

# 质量映射
#   1K → quality=low    (最快，~3秒/张)
#   2K → quality=medium  (标准，~8秒/张)
#   4K → quality=high    (最高清，~15秒/张)
IMAGE_QUALITY=auto
IMAGE_OUTPUT_FORMAT=png
IMAGE_BACKGROUND=auto
```

### 4.2 API 差异对照

| | DALL·E 3 | gpt-image-1 |
|---|---|---|
| **端点** | `/v1/images/generations` | `/v1/images/generations` |
| **参考图** | 不支持 | `/v1/images/edits`（multipart） |
| **尺寸** | 1024² / 1792×1024 / 1024×1792 | 1024² / 1024×1536 / 1536×1024 / auto |
| **质量** | standard / hd | low / medium / high / auto |
| **返回** | url 或 b64_json | 固定 b64_json |
| **response_format** | 支持 | **不支持**（传入会报错） |
| **output_format** | 不支持 | png / jpeg / webp |
| **background** | 不支持 | transparent / opaque / auto |

### 4.3 已实现的特性

- ✅ 自动区分 `gpt-image-1` 和 `dall-e-3`，走不同参数逻辑
- ✅ 有参考图时自动走 `/images/edits` 端点（仅 gpt-image-1）
- ✅ resolution → quality 自动映射（1K→low, 2K→medium, 4K→high）
- ✅ 参考图支持 data URI / 纯 base64 / 本地文件路径 三种格式
- ✅ 最多 4 张参考图

### 4.4 调用流程

```
用户上传产品图 → 创建项目 → 选择模块 → 点击生成
     ↓
后端读取产品图 → 转 base64 → 作为 reference_images 传入
     ↓
gpt-image-1 /images/edits 端点 → 返回 b64_json
     ↓
后端解码 → 保存到 projects/xxx/06_生成图片/模块名/ → 写入数据库
```

---

## 五、AI 思考与文案方案

### 方案 A：接入 LLM API（推荐生产环境）

```ini
TEXT_PROVIDER=openai
TEXT_API_KEY=sk-你的密钥
TEXT_BASE_URL=https://api.openai.com/v1
TEXT_MODEL=gpt-4o-mini
```

支持任何 OpenAI 兼容 API：GPT / Claude / Gemini / 国产模型。

### 方案 B：WorkBuddy 预生成模式（推荐开发阶段）

**原理**：用 WorkBuddy（当前工具）帮你思考，把结果存为知识库策略文件，本地运行时直接加载，不需要 LLM API。

**操作步骤**：

1. 用 WorkBuddy 生成行业策略：
   > "请为[服装行业]生成详情页策略 JSON，包含模块结构、摄影风格、色彩方案、各模块 Prompt 模板、不同市场的文案风格适配。"

2. 保存到 `knowledge/[行业]/strategy.json`

3. 本地运行时 `TEXT_PROVIDER=none`，系统自动加载策略文件作为回退

**优势**：
- 不需要额外的 API Key
- 策略可控、可审核
- 运行时零延迟（不需要等 API 返回）
- 适合离线开发

### 方案 C：纯模板模式（当前默认）

```ini
TEXT_PROVIDER=none
```

使用 `backend/app/utils/prompts.py` 中的内置行业模板。
适合最初期开发测试。

### 三种模式对比

| | 方案 A (LLM API) | 方案 B (WorkBuddy 预生成) | 方案 C (纯模板) |
|---|---|---|---|
| **需要 API Key** | ✅ 需要 | ❌ 不需要 | ❌ 不需要 |
| **生成质量** | 最高（实时推理） | 高（预生成策略） | 基础（固定模板） |
| **延迟** | 3-10秒 | 0（本地加载） | 0 |
| **灵活性** | 任意产品 | 策略覆盖的品类 | 固定模板 |
| **适合阶段** | 生产环境 | 开发 + 生产 | 初期开发 |

---

## 六、知识库建设指南

### 6.1 目录结构

```
knowledge/
├── [行业]/
│   ├── strategy.json          ← 行业策略
│   └── [品牌名]/
│       ├── analysis.json      ← 参考案例分析
│       └── screenshots/       ← 参考截图
```

### 6.2 用 WorkBuddy 批量生成策略

**Prompt 1：生成行业策略**
```
请为[美妆行业]生成详情页策略 JSON 文件，包含以下字段：
- page_structure: 模块顺序（参考通用 19 模块）、典型数量、信息密度
- photography_style: 光线、角度、背景、模特要求
- color_palette: 暖色调/冷色调/中性色系各 3 个色值
- prompt_templates: hero/pain_point/core_selling/feature/detail/scenario/spec_param 各一个 Prompt 模板
- copywriting: 卖点风格、CTA 风格、语气
- market_adaptation: zh-CN / en-US / ja-JP 三个市场的本地化策略
- reference_brands: 4 个推荐参考品牌
```

**Prompt 2：分析参考案例**
```
请分析这份[品牌名]详情页截图，输出为 JSON 格式的 visual_dna 分析文件：
- page_structure: 模块拆解和顺序
- visual_dna: 色彩体系、字体风格、摄影风格、布局比例
- prompt_analysis: 从截图反推各模块可能的生图 Prompt
- copywriting_analysis: 文案风格分析
```

### 6.3 已建策略

| 行业 | 策略文件 | 参考案例 |
|------|----------|----------|
| 服装 (apparel) | ✅ | lululemon ✅ |
| 3C 电子 (3c) | ✅ | apple (待填充) |
| 家居 (home) | ✅ | dyson (待填充) |
| 宠物 (pet) | ✅ | - |
| 其余 10 个行业 | 待生成 | - |

---

## 七、Codex 连续开发指令

以下 10 个 Skill 指令可以直接复制给 Codex/WorkBuddy 逐个执行。

### Skill 01：完善项目创建向导

```
在 AI 详情页工作台项目中，完善创建项目向导功能。

当前状态：6 步向导已跑通（产品图→行业→平台→AI帮写→语言/风格/比例→模块选择）。

需要改进：
1. 第 4 步「AI帮写」接入真实 LLM API 后，自动填充卖点/用户/视觉建议
2. 第 6 步模块选择支持拖拽排序
3. 模块数量支持每个模块独立设置（1-3张）
4. 创建项目后自动跳转到项目工作台

文件位置：
- 前端: frontend/src/pages/NewProjectPage.tsx
- 后端: backend/app/routers/projects.py, backend/app/routers/ai.py
- API: POST /api/projects/from-wizard, POST /api/ai/help-requirements
```

### Skill 02：AI 分析模块

```
在 AI 详情页工作台项目中，完善产品 AI 分析功能。

当前状态：ai_service.py 已有 plan_detail_page() 函数，支持 LLM API 调用和知识库回退。

需要改进：
1. 分析结果保存为「产品分析.md」到项目目录
2. 分析内容包括：产品定位、用户画像、核心卖点、详情页结构建议
3. 前端项目工作台展示分析结果
4. 支持手动编辑分析结果后重新生成

文件位置：
- 后端: backend/app/services/ai_service.py
- API: POST /api/ai/plan
- 知识库: knowledge/[行业]/strategy.json
```

### Skill 03：Prompt 生成模块

```
在 AI 详情页工作台项目中，完善 Prompt 自动生成功能。

当前状态：build_module_prompt() 使用通用模板，知识库策略有 prompt_templates。

需要改进：
1. 有 LLM API 时，用 AI 优化 Prompt（结合产品信息+行业策略+视觉风格）
2. 无 LLM 时，使用知识库 strategy.json 中的 prompt_templates
3. 每个模块的 Prompt 保存到项目目录的 prompts/ 文件夹
4. 前端支持查看和编辑 Prompt 后重新生成

文件位置：
- 后端: backend/app/utils/prompts.py (build_module_prompt)
- 后端: backend/app/services/ai_service.py (get_prompt_template)
- 后端: backend/app/routers/generation.py (_do_one_task 中的 prompt 构造)
```

### Skill 04：图片管理模块

```
在 AI 详情页工作台项目中，完善图片资产管理功能。

当前状态：图片按「项目/模块/」自动保存，支持预览/重生成/删除。

需要改进：
1. 图片支持标签（如「已选用」「备选」「废弃」）
2. 图片支持备注
3. 同模块多张图片支持排序
4. 图片库支持跨项目搜索（按标签/行业/模块）
5. 图片支持下载（单张/批量打包）

文件位置：
- 后端: backend/app/models/asset.py (Asset 模型需加 tags/notes 字段)
- 后端: backend/app/routers/files.py
- 前端: frontend/src/pages/ProjectDetailPage.tsx
```

### Skill 05：文档生成模块

```
在 AI 详情页工作台项目中，完善详情页文档自动生成功能。

当前状态：Word (docx) 和 HTML 导出已实现，PDF 未实现。

需要改进：
1. 接入 weasyprint 或 playwright 实现 PDF 导出
2. Word 文档增加封面页（产品名称+日期+版本）
3. Word 文档结构：封面→产品信息→页面结构→每个模块（图片+标题+正文+Prompt）
4. HTML 详情页优化为可直接部署到 Shopify 的格式
5. 导出时支持选择「含 Prompt」「含分析」等选项

文件位置：
- 后端: backend/app/services/document_service.py
- 后端: backend/app/routers/export.py
- API: POST /api/export/project/{id}?format=docx|html|pdf
```

### Skill 06：PDF 导出

```
在 AI 详情页工作台项目中，实现 PDF 导出功能。

方案：使用 weasyprint（纯 Python，不需要浏览器）。

步骤：
1. 安装 weasyprint: pip install weasyprint
2. 在 document_service.py 中添加 export_pdf() 方法
3. 将 HTML 详情页转为 PDF（复用 HTML 模板）
4. 在 export router 中添加 format=pdf 支持
5. 测试中英文混排和图片嵌入

文件位置：
- 后端: backend/app/services/document_service.py
- 后端: backend/app/routers/export.py
- 依赖: backend/requirements.txt (添加 weasyprint)
```

### Skill 07：视觉风格学习

```
在 AI 详情页工作台项目中，实现视觉风格分析功能。

目标：用户上传竞品详情页截图后，AI 分析其视觉 DNA 并用于后续生成。

步骤：
1. 在创建项目向导中增加「参考案例上传」步骤
2. 有 LLM API 时，调用视觉模型分析截图（色彩/构图/信息密度/摄影风格）
3. 无 LLM 时，用 Python PIL 提取主色调 + 布局比例
4. 分析结果保存为「视觉分析.json」
5. 生成图片时参考视觉 DNA

文件位置：
- 后端: 新建 backend/app/services/visual_analysis.py
- 后端: backend/app/routers/upload.py (增加分析接口)
- 前端: frontend/src/pages/NewProjectPage.tsx (增加上传步骤)
- 知识库: knowledge/[行业]/[品牌]/analysis.json
```

### Skill 08：历史项目管理

```
在 AI 详情页工作台项目中，完善历史项目管理功能。

当前状态：项目列表页已实现，支持查看所有项目。

需要改进：
1. 项目列表支持搜索（按名称/行业/状态）
2. 项目列表支持筛选（按行业/状态/创建时间）
3. 项目支持「复制」功能（基于已有项目快速创建新项目）
4. 项目支持「归档」状态
5. 项目详情页显示操作历史

文件位置：
- 前端: frontend/src/pages/ProjectsPage.tsx
- 后端: backend/app/routers/projects.py
- 后端: backend/app/models/project.py (添加 status 字段值：active/archived)
```

### Skill 09：模板管理

```
在 AI 详情页工作台项目中，实现模板管理功能。

目标：用户可以将成功的详情页结构保存为模板，下次快速复用。

步骤：
1. 新建 templates/ 目录存储模板
2. 模板格式：JSON（模块结构+行业+风格+Prompt 模板）
3. 项目工作台增加「保存为模板」按钮
4. 创建项目向导第 1 步增加「从模板开始」选项
5. 模板列表页支持预览和删除

文件位置：
- 后端: 新建 backend/app/routers/templates.py
- 后端: 新建 backend/app/models/template.py
- 前端: 新建 frontend/src/pages/TemplatesPage.tsx
- 存储: detail-page-studio/templates/
```

### Skill 10：Docker 服务器迁移

```
在 AI 详情页工作台项目中，完善 Docker 部署方案。

当前状态：Dockerfile 和 docker-compose.yml 已创建。

需要改进：
1. 测试 docker-compose up 一键启动（前端构建 + 后端 + nginx 反代）
2. 数据持久化：projects/ 和 knowledge/ 挂载为 volume
3. 环境变量通过 docker-compose.yml 的 env_file 注入
4. 添加健康检查（healthcheck）
5. 编写部署文档：从本地 Windows → Linux 服务器的迁移步骤

文件位置：
- backend/Dockerfile
- docker-compose.yml
- nginx.conf
- README.md (部署章节)
```

---

## 八、V1 开发路线图

### 第 1 周：核心流程打通

| 任务 | Skill | 优先级 |
|------|-------|--------|
| 接入 GPT Image API | 配置 .env | P0 |
| 接入 LLM API（文案/规划） | 配置 .env | P0 |
| AI 分析结果保存为 .md | Skill 02 | P1 |
| Prompt 生成优化 | Skill 03 | P1 |
| 端到端真实生图测试 | - | P0 |

### 第 2 周：文档与体验

| 任务 | Skill | 优先级 |
|------|-------|--------|
| PDF 导出 | Skill 06 | P1 |
| Word 文档优化（封面/Prompt） | Skill 05 | P1 |
| 图片标签与备注 | Skill 04 | P2 |
| 项目搜索与筛选 | Skill 08 | P2 |

### 第 3 周：知识库与模板

| 任务 | Skill | 优先级 |
|------|-------|--------|
| 生成全部 14 个行业策略 | 知识库 | P1 |
| 视觉风格分析 | Skill 07 | P2 |
| 模板管理 | Skill 09 | P2 |
| 参考案例管理 | - | P2 |

### 第 4 周：部署与优化

| 任务 | Skill | 优先级 |
|------|-------|--------|
| Docker 部署测试 | Skill 10 | P1 |
| 前端 UI 打磨 | - | P2 |
| 性能优化（并发生图） | - | P2 |
| 部署文档 | Skill 10 | P1 |

---

## 九、API 速查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| GET | /api/meta/industries | 行业列表 |
| GET | /api/meta/platforms | 平台列表 |
| GET | /api/meta/languages | 语言列表 |
| GET | /api/meta/styles | 视觉风格列表 |
| GET | /api/meta/modules | 模块列表 |
| GET | /api/meta/aspect-ratios | 比例列表 |
| GET | /api/meta/industry-preset/{industry} | 行业预设模块 |
| GET | /api/projects | 项目列表 |
| POST | /api/projects/from-wizard | 从向导创建项目 |
| GET | /api/projects/{id} | 项目详情 |
| PUT | /api/projects/{id} | 更新项目 |
| DELETE | /api/projects/{id} | 删除项目 |
| POST | /api/upload/{project_id} | 上传文件 |
| GET | /api/files | 读取文件（图片预览） |
| POST | /api/ai/plan | AI 规划详情页结构 |
| POST | /api/ai/help-requirements | AI 帮写 |
| POST | /api/generation/project/{id}/run | 批量生图 |
| GET | /api/generation/project/{id}/tasks | 任务列表 |
| GET | /api/generation/project/{id}/assets | 资产列表 |
| POST | /api/generation/task/{id}/retry | 单模块重试 |
| POST | /api/export/project/{id}?format=docx | 导出 Word |
| POST | /api/export/project/{id}?format=html | 导出 HTML |
| POST | /api/export/project/{id}?format=pdf | 导出 PDF（待实现） |

---

## 十、迁移路径

```
本地 Windows 开发
    ↓
Docker 本地运行（docker-compose up）
    ↓
Linux 服务器部署（Docker + nginx）
    ↓
未来：云服务器 + PostgreSQL + OSS/S3 对象存储
```

- 数据库：SQLite → PostgreSQL（改 DATABASE_URL 即可）
- 文件存储：本地 → OSS/S3（改 file_manager.py 的存储后端）
- 生图 API：不变（始终通过 .env 配置）
- 前端：Vite 构建 → nginx 静态文件
