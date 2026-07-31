"""Check which fields can be updated via __dict__"""
from app.config import settings

# 初始值
print("Initial state:")
print(f"  text_provider: {settings.text_provider}")
print(f"  text_model: {settings.text_model}")
print(f"  text_api_key: {settings.text_api_key!r}")
print()

# 逐个字段更新
settings.__dict__['text_provider'] = 'openai'
settings.__dict__['text_model'] = 'gpt-4o'
settings.__dict__['text_api_key'] = 'sk-test'

print("After __dict__ update:")
print(f"  text_provider: {settings.text_provider}")
print(f"  text_model: {settings.text_model}")
print(f"  text_api_key: {settings.text_api_key!r}")

# 通过 get_settings_service 看
from app.services.settings_service import get_settings
d = get_settings()
print()
print("get_settings() output:")
print(f"  text provider: {d['text']['provider']}")
print(f"  text model: {d['text']['model']}")
print(f"  text api_key_masked: {d['text']['api_key_masked']!r}")