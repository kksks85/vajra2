import requests
from urllib.parse import urlencode

# Create a session
session = requests.Session()

# Test with explicit content-type
data = {'username': 'admin', 'password': 'admin123'}

# Try different content types
print("Testing with form data (application/x-www-form-urlencoded):")
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
response = session.post('http://localhost:8000/login', data=data, headers=headers, allow_redirects=False)
print(f'Status: {response.status_code}')
print(f'Response: {response.text}')
print(f'Headers: {response.headers.get("location", "N/A")}')
