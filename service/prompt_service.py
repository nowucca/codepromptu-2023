import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from core import make_guid
from core.exceptions import (
    PromptException,
    RecordNotFoundError,
    ConstraintViolationError
)
from core.models import Prompt, User
from data import DatabaseContext
from data.prompt_repository import PromptRepositoryInterface
from .variables import VariablesService


class PromptServiceInterface():

    async def create_prompt(self, prompt: Prompt, user: User) -> str:
        pass

    async def update_prompt(self, prompt: Prompt) -> None:
        pass

    async def delete_prompt(self, guid: str) -> None:
        pass

    async def get_prompt(self, guid: str) -> Prompt:
        pass

    async def list_prompts(self) -> List[Prompt]:
        pass

    async def update_tags_for_prompt(self, guid: str, tags: List[str]) -> None:
        pass

    async def update_classification_for_prompt(self, guid: str, classification: str) -> None:
        pass

    async def search_prompts(self, query: str) -> List[Prompt]:
        pass

    async def get_prompts_by_tag(self, tag: str) -> List[Prompt]:
        pass

    async def get_prompts_by_classification(self, classification: str) -> List[Prompt]:
        pass

class PromptService(PromptServiceInterface):

    def __init__(self, repository: PromptRepositoryInterface):
        self.repo = repository
        self.variables_service = VariablesService()

    async def create_prompt(self, prompt: Prompt, author: Optional[User] = None) -> str:
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
            :param author:
        """
        try:
            self.variables_service.derive_variables(prompt)
            prompt.guid = make_guid()
            with DatabaseContext() as db:
                db.begin_transaction()
                guid = self.repo.create_prompt(prompt)
                db.commit_transaction()
                return guid
        except PromptException as known_exc:
            db.rollback_transaction()
            raise known_exc
        except Exception as e:
            db.rollback_transaction()
            raise PromptException("An unexpected error occurred while processing your request.") from e

    async def update_prompt(self, prompt: Prompt) -> None:
        """
        Update an existing prompt in the database.

        Args:
            prompt (Prompt): The prompt details with updated fields.

        Raises:
            PromptException: If any other exception is encountered.
            ConstraintViolationError: If a database constraint is violated.
            RecordNotFoundError: If the prompt isn't found in the DB.
        """
        try:
            self.variables_service.derive_variables(prompt)
            with DatabaseContext() as db:
                db.begin_transaction()
                self.repo.update_prompt(prompt)
                db.commit_transaction()
        except PromptException as known_exc:
            db.rollback_transaction()
            raise known_exc
        except Exception as e:
            db.rollback_transaction()
            raise PromptException("An unexpected error occurred while updating the prompt.") from e

    async def delete_prompt(self, guid: str) -> None:
        """
        Delete a prompt from the database using its GUID.

        Args:
            guid (str): The GUID of the prompt to be deleted.

        Raises:
            PromptException: If any other exception is encountered.
            ConstraintViolationError: If a database constraint is violated.
            RecordNotFoundError: If the prompt isn't found in the DB.
        """
        try:
            with DatabaseContext() as db:
                db.begin_transaction()
                self.repo.delete_prompt(guid)
                db.commit_transaction()
        except PromptException as known_exc:
            db.rollback_transaction()
            raise known_exc
        except Exception as e:
            db.rollback_transaction()
            raise PromptException("An unexpected error occurred while deleting the prompt.") from e

    async def get_prompt(self, guid: str) -> Prompt:
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
        try:
            with DatabaseContext():
                return self.repo.get_prompt(guid)
        except PromptException as known_exc:
            raise known_exc
        except Exception as e:
            raise PromptException("An unexpected error occurred while fetching the prompt.") from e

    async def list_prompts(self) -> List[Prompt]:
        """
        List all prompts in the database.

        Returns:
            List[Prompt]: A list of all prompts.

        Raises:
            PromptException: If any other exception is encountered.
        """
        try:
            with DatabaseContext():
                return self.repo.list_prompts()
        except Exception as e:
            raise PromptException("An unexpected error occurred while listing prompts.") from e

    async def update_tags_for_prompt(self, guid: str, tags: List[str]) -> None:
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
        try:
            with DatabaseContext() as db:
                db.begin_transaction()
                if tags:
                    self.repo.add_remove_tags_for_prompt(guid, tags)
                db.commit_transaction()
        except (ConstraintViolationError, RecordNotFoundError) as known_exc:
            db.rollback_transaction()
            raise known_exc
        except Exception as e:
            db.rollback_transaction()
            raise PromptException("An error occurred while updating tags for the prompt.") from e

    async def update_classification_for_prompt(self, guid: str, classification: str) -> None:
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
        try:
            with DatabaseContext() as db:
                db.begin_transaction()
                if classification:
                    self.repo.add_remove_classification_for_prompt(guid, classification)
                db.commit_transaction()
        except (ConstraintViolationError, RecordNotFoundError) as known_exc:
            db.rollback_transaction()
            raise known_exc
        except Exception as e:
            db.rollback_transaction()
            raise PromptException("An error occurred while updating classification for the prompt.") from e

    async def search_prompts(self, query: str) -> List[Prompt]:
        """
        Search for prompts based on a given query.
        """
        with DatabaseContext():
            return self.repo.search_prompts(query)

    async def get_prompts_by_tag(self, tag: str) -> List[Prompt]:
        """
        Retrieve all prompts associated with a specific tag.
        """
        with DatabaseContext():
            return self.repo.get_prompts_by_tag(tag)

    async def get_prompts_by_classification(self, classification: str) -> List[Prompt]:
        """
        Retrieve all prompts associated with a specific classification.
        """
        with DatabaseContext():
            return self.repo.get_prompts_by_classification(classification)

