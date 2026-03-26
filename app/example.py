from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(api_key)

if api_key: 
    print('API key: ' + api_key)
else:
    raise ValueError('API Key is not found. Check .env')


