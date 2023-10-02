from typing import Optional
from data.user_repository import UserRepositoryInterface
class UserServiceInterface:
    def get_user_by_username(self, username: str) -> Optional[dict]:
        pass


class UserService(UserServiceInterface):
    def __init__(self, repo: UserRepositoryInterface):
        self.repo = repo

    def get_user_by_username(self, username: str) -> Optional[dict]:
        return self.repo.get_user_by_username(username)
