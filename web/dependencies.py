from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

from data.prompt_repository import MySQLPromptRepository, PromptRepositoryInterface
from data.user_repository import MySQLUserRepository, UserRepositoryInterface
from service.prompt_service import PromptServiceInterface, PromptService
from service.user_service import UserServiceInterface, UserService

security = HTTPBasic()


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> dict:
    user = UserService().get_user_by_username(credentials.username)

    if user is None or not secrets.compare_digest(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return user


def get_prompt_repository() -> PromptRepositoryInterface:
    return MySQLPromptRepository()


def get_user_repository() -> UserRepositoryInterface:
    return MySQLUserRepository()


def get_prompt_service(repo: PromptRepositoryInterface = Depends(get_prompt_repository)) -> PromptServiceInterface:
    return PromptService(repo)


def get_user_service(repo: UserRepositoryInterface = Depends(get_user_repository)) -> UserServiceInterface:
    return UserService(repo)
