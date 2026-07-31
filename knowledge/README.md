# 详情页知识库 (Knowledge Base)

> 这里是 AI 详情页工作台的"大脑"——所有行业策略、参考案例、Prompt 模板的存储中心。

## 目录结构

```
knowledge/
├── README.md                    ← 本文件
├── apparel/
│   ├── strategy.json            ← 服装行业策略（模块结构 + 风格 + Prompt 模板）
│   └── lululemon/
│       ├── analysis.json        ← 参考案例结构分析
│       └── screenshots/         ← 参考截图（手动放入）
├── 3c/
│   ├── strategy.json
│   └── apple/
│       └── analysis.json
├── home/
│   ├── strategy.json
│   └── dyson/
│       └── analysis.json
├── pet/
│   └── strategy.json
├── ...
└── _shared/
    ├── prompt_library.json      ← 跨行业通用 Prompt 库
    └── color_systems.json       ← 色彩体系参考
```

## 两种知识文件

### 1. 行业策略 `strategy.json`

每个行业一份，包含：
- **page_structure**: 模块顺序、数量、信息密度
- **photography_style**: 光线、角度、背景、模特要求
- **color_palette**: 推荐色系
- **prompt_templates**: 各模块的 Prompt 模板（含变量占位符）
- **copywriting**: 文案风格指南
- **market_adaptation**: 不同市场的本地化策略
- **reference_brands**: 推荐参考品牌

→ AI 规划详情页结构时优先读取这份策略，而不是每次从零推理。

### 2. 参考案例 `brand_name/analysis.json`

对优秀详情页的结构化分析：
- **page_structure**: 模块拆解
- **visual_dna**: 色彩、字体、摄影、布局的"视觉基因"
- **prompt_analysis**: 从截图反推可能的生图 Prompt
- **copywriting_analysis**: 文案风格分析

→ 生成详情页时参考这些"视觉 DNA"，保持风格一致性。

## 如何扩展

### 添加新行业
1. 在 `knowledge/` 下创建行业目录
2. 创建 `strategy.json`（可复制现有行业作为模板）
3. 更新 `backend/app/utils/prompts.py` 中的 `INDUSTRIES` 列表

### 添加参考案例
1. 在对应行业目录下创建品牌文件夹
2. 截图放入 `screenshots/` 子目录
3. 创建 `analysis.json` 记录结构分析
4. 也可以让 WorkBuddy 帮你分析截图并生成 analysis.json

### 用 WorkBuddy 批量生成策略
```
提示词示例：
"请参考 lululemon 官网详情页截图，分析其页面结构、视觉风格、
色彩体系、摄影风格、文案风格，输出为 JSON 格式的 visual_dna 分析文件。"
```

## 与后端的集成

后端 `ai_service.py` 已支持：
1. **有 LLM API 时**：调用 LLM + 知识库策略作为 system prompt 上下文
2. **无 LLM API 时**：直接使用 `strategy.json` 作为模板回退

未来计划：
- [ ] 添加 `/api/knowledge/industries` API 列出所有可用策略
- [ ] 添加 `/api/knowledge/cases` API 列出参考案例
- [ ] 支持从 Web 界面上传截图并自动生成 analysis.json
