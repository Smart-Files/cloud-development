import asyncio
from functools import partial
from typing import Callable

from langchain_openai import ChatOpenAI
from langchain.tools import Tool

ask_user_event = asyncio.Event()

async def ask_clarification_factory(uuid: str) -> Callable[[str], None]:
    return partial(ask_clarification, uuid)


async def ask_clarification(uuid: str, query: str):
    """
    Ask the user for clarification on the given query.
    """
    
    print(f"Ask clarification for: {query}")
    await ask_user_event.wait()
     

