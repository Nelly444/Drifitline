import pytest
from fastapi_users.exceptions import InvalidPasswordException

from app.auth import UserManager


@pytest.mark.asyncio
async def test_rejects_password_shorter_than_8_characters():
    manager = UserManager(user_db=None)

    with pytest.raises(InvalidPasswordException):
        await manager.validate_password("short1", user=None)


@pytest.mark.asyncio
async def test_accepts_password_of_8_or_more_characters():
    manager = UserManager(user_db=None)

    await manager.validate_password("longenough1", user=None)
