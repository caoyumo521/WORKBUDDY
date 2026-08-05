"""统一配置中心 - 所有可调参数都从这里读取，禁止在代码里硬编码。"""
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- 服务 ----
    app_host: str = "0.0.0.0"
    app_port: int = 8091
    app_debug: bool = True
    # 字符串形式，逗号分隔；通过 cors_origins property 转 list
    app_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

    # ---- 存储 ----
    projects_root: Path = BACKEND_DIR.parent / "projects"

    # ---- 知识库 ----
    knowledge_root: Path = BACKEND_DIR.parent / "knowledge"

    # ---- 数据库 ----
    database_url: str = f"sqlite:///{BACKEND_DIR / 'detail_studio.db'}"

    # ---- 生图 ----
    # provider: openai | flux | custom | mock
    # model 举例:
    #   - gpt-image-2 / gpt-image-1 (GPT Image API, 支持参考图编辑)
    #   - dall-e-3   (DALL·E 3, 经典文生图)
    #   - flux-pro   (Flux 系列)
    image_provider: str = "mock"
    image_api_key: str = ""
    image_base_url: str = "https://api.openai.com/v1"
    image_model: str = "gpt-image-2"
    # gpt-image 专用: low | medium | high | auto
    image_quality: str = "auto"
    # gpt-image 专用: png | jpeg | webp
    image_output_format: str = "png"
    # gpt-image 专用: transparent | opaque | auto
    image_background: str = "auto"

    # ---- 生图多中转（容灾）----
    # JSON 数组，每项 {base_url, api_key, model}
    # 依次尝试，第一个成功的即用；全部失败才报错
    # 例: [{"base_url":"https://a/v1","api_key":"sk-xxx","model":"gpt-image-2"}]
    # 留空则回退到上面的单 Key 配置（IMAGE_API_KEY / IMAGE_BASE_URL / IMAGE_MODEL）
    image_relays: str = ""

    # ---- 文案 / 规划 LLM ----
    # provider:
    #   openai    → 标准 OpenAI 兼容 API
    #   workbuddy  → WorkBuddy 内置 AI（开发时用 WorkBuddy 帮你思考/写文案，
    #               预生成策略文件到 knowledge/ 目录，运行时直接加载）
    #   none      → 不调用 LLM，纯模板模式
    text_provider: str = "none"
    text_api_key: str = ""
    text_base_url: str = "https://api.openai.com/v1"
    text_model: str = "gpt-4o-mini"

    # ---- 详情页文字合成（A 层 AI 画标题 + B 层 PIL 叠信息层）----
    # 总开关：关闭后只出纯图，不做任何文字合成
    text_overlay_enabled: bool = True
    # 是否让生图模型直接把中文主标题画进画面（版式融合度更高，但可能出错别字）
    # 关闭时主标题也改由 PIL 叠加，绝对不会错字但版式融合度略低
    ai_render_headline: bool = True
    # 生成后用视觉模型检查 AI 画的中文是否正确；发现错字自动用 PIL 覆盖修正
    text_qc_enabled: bool = True
    # 中文字体路径覆盖（留空则自动探测系统字体：Windows 微软雅黑 / macOS 苹方 / Linux Noto）
    text_overlay_font_bold: str = ""
    text_overlay_font_regular: str = ""

    # ---- 通用 ----
    default_image_resolution: str = "2K"
    supported_resolutions: str = "1K,2K,4K"

    @field_validator("projects_root")
    @classmethod
    def ensure_projects_root(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("knowledge_root")
    @classmethod
    def ensure_knowledge_root(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v

    @property
    def supported_resolution_list(self) -> List[str]:
        return [x.strip() for x in self.supported_resolutions.split(",") if x.strip()]

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def has_text_llm(self) -> bool:
        """是否配置了可用的文本 LLM。"""
        return self.text_provider not in ("none", "") and bool(self.text_api_key)


settings = Settings()
