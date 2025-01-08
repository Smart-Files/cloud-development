import uuid as uuid_lib
import asyncio
from typing import Any, Dict, List
from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from project.firestore import db, firestore_app
from project.logger import logger


class FirestoreCallbackHandler(AsyncCallbackHandler):
    """Async callback handler that can be used to handle callbacks from langchain."""
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Run when chain starts running."""
        run_id = str(uuid_lib.uuid4())
        data = {"event": "on_llm_start", "run_id": run_id, "prompts": prompts}
        logger.info("DATA: " + str(data))
        process_doc = db.collection("process").document(self.uuid)
        run_doc = process_doc.collection("data").document(run_id)
        await run_doc.set(data)

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run when a new token is generated."""
        run_id = str(uuid_lib.uuid4())
        data = {"event": "on_llm_new_token", "run_id": run_id, "token": token}
        logger.info("DATA: " + str(data))
        process_doc = db.collection("process").document(self.uuid)
        run_doc = process_doc.collection("data").document(run_id)
        await run_doc.set(data, merge=True)

    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when chain ends running."""
        run_id = str(uuid_lib.uuid4())
        data = {"event": "on_llm_end", "run_id": run_id, "response": response.dict()}
        logger.info("DATA: " + str(data))
        process_doc = db.collection("process").document(self.uuid)
        run_doc = process_doc.collection("data").document(run_id)
        await run_doc.set(data, merge=True)