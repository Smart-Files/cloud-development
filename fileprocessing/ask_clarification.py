import asyncio
from fileprocessing import state

ask_user_event = asyncio.Event()

async def ask_clarification(query: str):
    """
    Ask the user for clarification on the given query.
    """
    uuid = state.get_current_uuid()
    print(f"Ask clarification for {uuid}")
    await ask_user_event.wait()
    print(f"Ask clarification for {uuid}")
     

