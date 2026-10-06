import os
os.environ["DATABASE_URL"]="sqlite:///./test.db"
import pytest
from fastapi.testclient import TestClient
from app.db import Base,engine
from app.main import app
@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine); yield
@pytest.fixture
def client(): return TestClient(app)
