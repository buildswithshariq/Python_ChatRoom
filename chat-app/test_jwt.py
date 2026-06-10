import os
from datetime import datetime, timedelta, timezone
from jose import jwt
SECRET_KEY = "dev-secret-key-change-in-production-abc123xyz"
ALGORITHM = "HS256"

data = {"sub": "1"}
expire = datetime.now(timezone.utc) + timedelta(minutes=60)
data.update({"exp": expire})

try:
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    print("Token:", token)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("Payload:", payload)
except Exception as e:
    print("Error:", e)
