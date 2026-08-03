from fastapi import APIRouter, Depends, Response, status

from app.auth import UserManager, current_active_user, get_user_manager
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
) -> Response:
    await user_manager.delete(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
