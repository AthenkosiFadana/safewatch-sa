import os
import sys
import tempfile

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

# Use an isolated throwaway database for every test session
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_PATH"] = _tmp.name
os.environ["STORAGE_BACKEND"] = "sqlite"
os.environ["RATE_LIMIT_PER_HOUR"] = "1000"

import pytest  # noqa: E402

from app import create_app  # noqa: E402
from app.auth import hash_password  # noqa: E402
from services import storage  # noqa: E402


@pytest.fixture(scope="session")
def app():
    application = create_app({"TESTING": True})
    storage.init_db()
    db = storage.get_db()
    db.insert_user({
        "userId": "USR-TESTADMIN",
        "email": "admin@test.local",
        "name": "Test Admin",
        "passwordHash": hash_password("Admin123!"),
        "community": "Central, Gqeberha",
        "role": "ADMIN",
        "createdAt": storage.utcnow(),
    })
    db.insert_user({
        "userId": "USR-TESTMEMBER",
        "email": "member@test.local",
        "name": "Test Member",
        "passwordHash": hash_password("Member123!"),
        "community": "New Brighton",
        "role": "MEMBER",
        "createdAt": storage.utcnow(),
    })
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def member(client):
    token = client.post("/api/auth/login", json={"email": "member@test.local", "password": "Member123!"}).json["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin(client):
    token = client.post("/api/auth/login", json={"email": "admin@test.local", "password": "Admin123!"}).json["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_incident():
    return {
        "category": "THEFT",
        "description": "Vehicle break-in reported near the shopping centre",
        "area": "Central, Gqeberha",
        "severity": "HIGH",
        "latitude": -33.9614,
        "longitude": 25.6022,
    }
