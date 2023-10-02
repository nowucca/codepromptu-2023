from abc import ABC, abstractmethod
from typing import List

from core.exceptions import (
    PromptException,
    RecordNotFoundError,
    ConstraintViolationError
)
from core.models import Prompt
from data import DatabaseContext
from data.prompt_repository import PromptRepositoryInterface
from .variables import VariablesService


class PromptServiceInterface(ABC):

    @abstractmethod
    def create_prompt(self, prompt: Prompt) -> str:
        pass

    @abstractmethod
    def update_prompt(self, prompt: Prompt) -> None:
        pass

    @abstractmethod
    def delete_prompt(self, guid: str) -> None:
        pass

    @abstractmethod
    def get_prompt(self, guid: str) -> Prompt:
        pass

    @abstractmethod
    def list_prompts(self) -> List[Prompt]:
        pass

    @abstractmethod
    def update_tags_for_prompt(self, guid: str, tags: List[str]) -> None:
        pass

    @abstractmethod
    def update_classification_for_prompt(self, guid: str, classification: str) -> None:
        pass


class PromptService(PromptServiceInterface):

    def __init__(self, repository: PromptRepositoryInterface):
        self.repo = repository
        self.variables_service = VariablesService()

    def create_prompt(self, prompt: Prompt) -> str:
        """
        Create a new prompt in the database.

        Args:
            prompt (Prompt): The prompt details.

        Returns:
            str: The GUID of the created prompt.

        Raises:
            PromptException: If any other exception is encountered.
            DataValidationError: If the provided prompt is invalid or if there's a validation error in the DB layer.
            ConstraintViolationError: If a database constraint is violated.
        """
        try:
            self.variables_service.derive_variables(prompt)
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

    def update_prompt(self, prompt: Prompt) -> None:
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

    def delete_prompt(self, guid: str) -> None:
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

    def get_prompt(self, guid: str) -> Prompt:
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
            return self.repo.get_prompt(guid)
        except PromptException as known_exc:
            raise known_exc
        except Exception as e:
            raise PromptException("An unexpected error occurred while fetching the prompt.") from e

    def list_prompts(self) -> List[Prompt]:
        """
        List all prompts in the database.

        Returns:
            List[Prompt]: A list of all prompts.

        Raises:
            PromptException: If any other exception is encountered.
        """
        try:
            return self.repo.list_prompts()
        except Exception as e:
            raise PromptException("An unexpected error occurred while listing prompts.") from e

    def update_tags_for_prompt(self, guid: str, tags: List[str]) -> None:
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

    def update_classification_for_prompt(self, guid: str, classification: str) -> None:
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

