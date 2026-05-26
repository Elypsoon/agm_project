from cryptography.fernet import Fernet
import time

key = 'SvbCwnUtbAqtL99brX-d4JInxg0-dsChsQWvLkCErNY='
f = Fernet(key.encode())
timestamp = int(time.time())
payload = f'550e8400-e29b-41d4-a716-446655440002:A21234567:1bed8a79-4d1b-4ae9-9c3c-dc37f8a55106:{timestamp}'
token = f.encrypt(payload.encode()).decode()
print(token)