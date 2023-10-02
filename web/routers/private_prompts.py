from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from core.models import Prompt
from service.prompt_service import PromptServiceInterface
from web.dependencies import get_current_user, get_prompt_service

router = APIRouter(dependencies=[Depends(get_current_user), Depends(get_prompt_service)])

@router.post("/", status_code=201, summary="Add a New Prompt")
async def add_prompt(prompt: Prompt, service: PromptServiceInterface = Depends()):
    return await service.create_prompt(prompt)


@router.delete("/{guid}", status_code=204, summary="Delete a Prompt by GUID")
async def delete_prompt(guid: str, service: PromptServiceInterface = Depends()):
    await service.delete_prompt(guid)
    return {}  # Return an empty response for 204 status


@router.put("/{guid}", summary="Update a Prompt by GUID")
async def update_prompt(guid: str, prompt: Prompt, service: PromptServiceInterface = Depends()):
    assert guid == prompt.guid
    return await service.update_prompt(prompt)


@router.get("/search", response_model=List[Prompt], summary="Search Prompts")
async def search_prompts(query: str, service: PromptServiceInterface = Depends()):
    return await service.search_prompts(query)


@router.get("/tags/{tag}/", response_model=List[Prompt], summary="List Prompts by Tag")
async def get_prompts_by_tag(tag: str, service: PromptServiceInterface = Depends()):
    return await service.get_prompts_by_tag(tag)


@router.get("/classification/{classification}/", response_model=List[Prompt], summary="List Prompts by Classification")
async def get_prompts_by_classification(classification: str, service: PromptServiceInterface = Depends()):
    return await service.get_prompts_by_classification(classification)
