import requests

# Create a session to handle cookies
session = requests.Session()

# Test login with POST request
data = {'username': 'admin', 'password': 'admin123'}
response = session.post('http://localhost:8000/login', data=data, allow_redirects=False)
print(f'Login Status: {response.status_code}')
print(f'Response Text: {response.text}')
print(f'Cookies: {session.cookies}')
print(f'Headers: {dict(response.headers)}')

