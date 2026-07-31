from app.config import settings
print('Before:')
print(f'  text_api_key = {settings.text_api_key!r}')

# Try clearing
settings.__dict__['text_api_key'] = ''
print('After __dict__ clear:')
print(f'  text_api_key = {settings.text_api_key!r}')