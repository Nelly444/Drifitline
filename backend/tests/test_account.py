import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth import current_active_user, get_user_manager
from app.main import app

client = TestClient(app)


class FakeUser:
    def __init__(self, id, is_active=True):
        self.id = id
        self.is_active = is_active


class FakeUserManager:
    def __init__(self):
        self.deleted_users = []

    async def delete(self, user, request=None):
        self.deleted_users.append(user)


@pytest.fixture
def fake_user_manager():
    return FakeUserManager()


@pytest.fixture(autouse=True)
def override_dependencies(fake_user_manager):
    user = FakeUser(id=uuid.uuid4())
    app.dependency_overrides[current_active_user] = lambda: user
    app.dependency_overrides[get_user_manager] = lambda: fake_user_manager
    yield user
    app.dependency_overrides.pop(current_active_user, None)
    app.dependency_overrides.pop(get_user_manager, None)


def test_delete_me_deletes_the_current_user(fake_user_manager, override_dependencies):
    response = client.delete("/users/me")

    assert response.status_code == 204
    assert fake_user_manager.deleted_users == [override_dependencies]
