from app.config import settings
print('Before:')
print('  text_provider:', settings.text_provider)
print('  text_model:', settings.text_model)
print('  text_api_key:', settings.text_api_key)
print()

settings.__dict__['text_provider'] = 'openai'
settings.__dict__['text_model'] = 'gpt-4o'
settings.__dict__['text_api_key'] = 'sk-test1234'

print('After:')
print('  text_provider:', settings.text_provider)
print('  text_model:', settings.text_model)
print('  text_api_key:', settings.text_api_key)
print()
print('__dict__:')
for k, v in sorted(settings.__dict__.items()):
    if 'text' in k.lower() or 'TEXT' in k:
        print(f'  {k} = {v!r}')