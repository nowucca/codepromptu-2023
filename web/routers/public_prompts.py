from fastapi import APIRouter, Depends, HTTPException, Query

from core.exceptions import RecordNotFoundError
from core.models import Prompt
from service.prompt_service import PromptServiceInterface
from typing import List

router = APIRouter()


@router.get("/{guid}", response_model=Prompt, summary="Retrieve a Prompt by GUID")
def get_prompt(guid: str, service: PromptServiceInterface = Depends()):
    try:
        return service.get_prompt(guid)
    except RecordNotFoundError:
        raise HTTPException(status_code=404, detail="Prompt not found")


@router.get("/", response_model=List[Prompt], summary="List all Public Prompts")
def list_prompts(skip: int = 0, limit: int = 10, service: PromptServiceInterface = Depends()):
    # Using pagination with skip and limit.
    # You can enhance this further by allowing filters like tags, authors, etc.
    return service.list_prompts()[skip: skip+limit]


@router.get("/search/", response_model=List[Prompt], summary="Search Prompts")
def search_prompts(query: str, service: PromptServiceInterface = Depends()):
    # Assuming the service has a method to search prompts. This can be implemented in various ways.
    return service.search_prompts(query)


@router.get("/tags/{tag}", response_model=List[Prompt], summary="List Prompts by Tag")
def get_prompts_by_tag(tag: str, service: PromptServiceInterface = Depends()):
    # Assuming the service has a method to get prompts by tag.
    return service.get_prompts_by_tag(tag)


@router.get("/classification/{classification}", response_model=List[Prompt], summary="List Prompts by Classification")
def get_prompts_by_classification(classification: str, service: PromptServiceInterface = Depends()):
    # Assuming the service has a method to get prompts by classification.
    return service.get_prompts_by_classification(classification)
