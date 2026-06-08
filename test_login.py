import requests

# Test login with POST request
data = {'username': 'admin', 'password': 'admin123'}
try:
    response = requests.post('http://localhost:8000/login', data=data, allow_redirects=False)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type")}')
    if 'location' in response.headers:
        print(f'Location: {response.headers["location"]}')
    if response.status_code >= 400:
        print(f'Error: {response.text[:1000]}')
    else:
        print('Login successful!')
except Exception as e:
    print(f'Error: {e}')
