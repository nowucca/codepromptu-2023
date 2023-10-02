import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from core import make_guid
from core.exceptions import (
    PromptException,
    RecordNotFoundError,
    ConstraintViolationError
)
from core.models import Prompt, User, PromptCreate, PromptUpdate
from data import DatabaseContext
from data.prompt_repository import PromptRepositoryInterface
from .variables_service import VariablesService


class PromptServiceInterface:

    def create_prompt(self, prompt: PromptCreate, author: Optional[User] = None) -> str:
        pass

    def update_prompt(self, prompt: PromptUpdate, user: Optional[User] = None) -> None:
        pass

    def delete_prompt(self, guid: str, user: Optional[User] = None) -> None:
        pass

    def get_prompt(self, guid: str, user: Optional[User] = None) -> Prompt:
        pass

    def list_prompts(self, user: Optional[User] = None) -> List[Prompt]:
        pass

    def update_tags_for_prompt(self, guid: str, tags: List[str], user: Optional[User] = None) -> None:
        pass

    def update_classification_for_prompt(self, guid: str, classification: str, user: Optional[User] = None) -> None:
        pass

    def search_prompts(self, query: str, user: Optional[User] = None) -> List[Prompt]:
        pass

    def get_prompts_by_tag(self, tag: str, user: Optional[User] = None) -> List[Prompt]:
        pass

    def get_prompts_by_classification(self, classification: str, user: Optional[User] = None) -> List[Prompt]:
        pass

class PromptService(PromptServiceInterface):

    def __init__(self, repository: PromptRepositoryInterface):
        self.repo = repository
        self.variables_service = VariablesService()

    def create_prompt(self, prompt: PromptCreate, author: Optional[User] = None) -> str:
        """
        Create a new prompt in the database.

        Args:
            prompt (Prompt): The prompt details.
            author (User): The user creating the prompt.

        Returns:
            str: The GUID of the created prompt.

        Raises:
            PromptException: If any other exception is encountered.
            DataValidationError: If the provided prompt is invalid or if there's a validation error in the DB layer.
            ConstraintViolationError: If a database constraint is violated.
            :param prompt:
            :param author:
        """
        with DatabaseContext() as db:
            try:
                self.variables_service.derive_variables(prompt)
                db.begin_transaction()
                guid = self.repo.create_prompt(prompt, author)
                db.commit_transaction()
                return guid
            except PromptException as known_exc:
                db.rollback_transaction()
                raise known_exc
            except Exception as e:
                db.rollback_transaction()
                raise PromptException("An unexpected error occurred while processing your request.") from e

    def update_prompt(self, prompt: PromptUpdate, user: Optional[User] = None) -> None:
        """
        Update an existing prompt in the database.

        Args:
            prompt (Prompt): The prompt details with updated fields.

        Raises:
            PromptException: If any other exception is encountered.
            ConstraintViolationError: If a database constraint is violated.
            RecordNotFoundError: If the prompt isn't found in the DB.
            :param user:
        """
        with DatabaseContext() as db:

            try:
                self.variables_service.derive_variables(prompt)
                db.begin_transaction()
                self.repo.update_prompt(prompt, user)
                db.commit_transaction()
            except PromptException as known_exc:
                db.rollback_transaction()
                raise known_exc
            except Exception as e:
                db.rollback_transaction()
                raise PromptException("An unexpected error occurred while updating the prompt.") from e

    def delete_prompt(self, guid: str, user: Optional[User] = None) -> None:
        """
        Delete a prompt from the database using its GUID.

        Args:
            guid (str): The GUID of the prompt to be deleted.

        Raises:
            PromptException: If any other exception is encountered.
            ConstraintViolationError: If a database constraint is violated.
            RecordNotFoundError: If the prompt isn't found in the DB.
        """
        with DatabaseContext() as db:
            try:
                db.begin_transaction()
                self.repo.delete_prompt(guid, user)
                db.commit_transaction()
            except PromptException as known_exc:
                db.rollback_transaction()
                raise known_exc
            except Exception as e:
                db.rollback_transaction()
                raise PromptException("An unexpected error occurred while deleting the prompt.") from e

    def get_prompt(self, guid: str, user: Optional[User] = None) -> Prompt:
        """
        Retrieve a prompt from the database using its GUID.

        Args:
            guid (str): The GUID of the prompt to be fetched.

        Returns:
            Prompt: The retrieved prompt details.

        Raises:
            PromptException: If any other exception is encountered.
            RecordNotFoundError: If the prompt isn't found in the DB.
        """
        with DatabaseContext():
            try:
                return self.repo.get_prompt(guid, user)
            except PromptException as known_exc:
                raise known_exc
            except Exception as e:
                raise PromptException("An unexpected error occurred while fetching the prompt.") from e

    def list_prompts(self, user: Optional[User] = None) -> List[Prompt]:
        """
        List all prompts in the database.

        Returns:
            List[Prompt]: A list of all prompts.

        Raises:
            PromptException: If any other exception is encountered.
        """
        with DatabaseContext():
            try:
                return self.repo.list_prompts(user)
            except Exception as e:
                raise PromptException("An unexpected error occurred while listing prompts.") from e

    async def update_tags_for_prompt(self, guid: str, tags: List[str], user: Optional[User] = None) -> None:
        """
        Add or remove tags for a given prompt in the database.

        Args:
            guid (str): The GUID of the prompt to be updated.
            tags (List[str]): List of tags to be associated with the prompt.

        Raises:
            PromptException: If any other exception is encountered.
            ConstraintViolationError: If a database constraint is violated.
            RecordNotFoundError: If the prompt isn't found in the DB.
        """
        with DatabaseContext() as db:
            try:
                db.begin_transaction()
                if tags:
                    self.repo.add_remove_tags_for_prompt(guid, tags, user)
                db.commit_transaction()
            except (ConstraintViolationError, RecordNotFoundError) as known_exc:
                db.rollback_transaction()
                raise known_exc
            except Exception as e:
                db.rollback_transaction()
                raise PromptException("An error occurred while updating tags for the prompt.") from e

    async def update_classification_for_prompt(self, guid: str, classification: str, user: Optional[User] = None) -> None:
        """
        Add or remove classifications for a given prompt in the database.

        Args:
            guid (str): The GUID of the prompt to be updated.
            classification: Classifications to be associated with the prompt.

        Raises:
            PromptException: If any other exception is encountered.
            ConstraintViolationError: If a database constraint is violated.
            RecordNotFoundError: If the prompt isn't found in the DB.
        """
        with DatabaseContext() as db:
            try:
                db.begin_transaction()
                if classification:
                    self.repo.add_remove_classification_for_prompt(guid, classification, user)
                db.commit_transaction()
            except (ConstraintViolationError, RecordNotFoundError) as known_exc:
                db.rollback_transaction()
                raise known_exc
            except Exception as e:
                db.rollback_transaction()
                raise PromptException("An error occurred while updating classification for the prompt.") from e

    def search_prompts(self, query: str, user: Optional[User] = None) -> List[Prompt]:
        """
        Search for prompts based on a given query.
        """
        with DatabaseContext():
            return self.repo.search_prompts(query, user)

    def get_prompts_by_tag(self, tag: str, user: Optional[User] = None) -> List[Prompt]:
        """
        Retrieve all prompts associated with a specific tag.
        """
        with DatabaseContext():
            return self.repo.get_prompts_by_tag(tag, user)

    def get_prompts_by_classification(self, classification: str, user: Optional[User] = None) -> List[Prompt]:
        """
        Retrieve all prompts associated with a specific classification.
        """
        with DatabaseContext():
            return self.repo.get_prompts_by_classification(classification, user)

