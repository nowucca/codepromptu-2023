from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from core.models import Prompt, User
from service.prompt_service import PromptServiceInterface
from web.dependencies import get_current_user, get_prompt_service

router = APIRouter()

@router.get("/login", status_code=204, summary="Test Login")
async def test_login(service: PromptServiceInterface = Depends(get_prompt_service),
                     user: User = Depends(get_current_user)):
    print(f"Login successful user={user}   service={service}")
    return


@router.post("/prompt/", status_code=201, summary="Add a New Prompt")
async def add_prompt(prompt: Prompt, service: PromptServiceInterface = Depends(), user: User = Depends()):
    return await service.create_prompt(prompt, user)


@router.delete("/prompt/{guid}", status_code=204, summary="Delete a Prompt by GUID")
async def delete_prompt(guid: str, service: PromptServiceInterface = Depends()):
    await service.delete_prompt(guid)
    return {}  # Return an empty response for 204 status


@router.put("/prompt/{guid}", summary="Update a Prompt by GUID")
async def update_prompt(guid: str, prompt: Prompt, service: PromptServiceInterface = Depends()):
    assert guid == prompt.guid
    return await service.update_prompt(prompt)


@router.get("/prompt/search", response_model=List[Prompt], summary="Search Prompts")
async def search_prompts(query: str, service: PromptServiceInterface = Depends()):
    return await service.search_prompts(query)


@router.get("/prompt/tags/{tag}/", response_model=List[Prompt], summary="List Prompts by Tag")
async def get_prompts_by_tag(tag: str, service: PromptServiceInterface = Depends()):
    return await service.get_prompts_by_tag(tag)


@router.get("/prompt/classification/{classification}/", response_model=List[Prompt], summary="List Prompts by Classification")
async def get_prompts_by_classification(classification: str, service: PromptServiceInterface = Depends()):
    return await service.get_prompts_by_classification(classification)
