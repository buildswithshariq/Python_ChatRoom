from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

response = client.post(
    "/auth/register",
    data={"username": "testuser", "email": "test@test.com", "password": "password123"}
)
print("Register Status:", response.status_code)
print("Register Headers:", response.headers)

# TestClient automatically handles cookies
response2 = client.get("/rooms", follow_redirects=False)
print("Rooms Status:", response2.status_code)
print("Rooms Headers:", response2.headers)
print("Rooms Content:", response2.text[:100])
