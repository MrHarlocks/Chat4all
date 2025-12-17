from src.adapters.db.user_repository import UserRepository
from src.domain.models import User, Platform
from uuid import UUID, uuid4

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    async def get_or_create_user(self, user_id: UUID = None, display_name: str = None) -> User:
        if user_id:
            user = await self.repository.get_by_id(user_id)
            if user:
                return user
            # If ID provided but not found, create with that ID
            new_user = User(
                id=user_id,
                platform=Platform.INTERNAL,
                platform_id=str(user_id),
                display_name=display_name or f"User {str(user_id)[:8]}"
            )
            return await self.repository.create(new_user)
        
        if display_name:
            user = await self.repository.get_by_display_name(display_name)
            if user:
                return user

        # No ID provided and not found by name, create new
        new_id = uuid4()
        new_user = User(
            id=new_id,
            platform=Platform.INTERNAL,
            platform_id=str(new_id),
            display_name=display_name or f"User {str(new_id)[:8]}"
        )
        return await self.repository.create(new_user)
