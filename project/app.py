import asyncio
import datetime
import json
from typing import Callable
import fastapi
from pydantic import BaseModel
from project import tools_agent
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware as CORSMiddleware
from langchain_core.tools import Tool
from langchain_core.messages.ai import AIMessage
from langchain.memory.buffer import ConversationBufferMemory
from langchain.agents import AgentExecutor, create_react_agent, create_json_chat_agent, create_tool_calling_agent, initialize_agent
from langchain_core.agents import AgentAction, AgentStep, HumanMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain.tools import BaseTool
from langchain_core.runnables.utils import AddableDict
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.messages.system import SystemMessage
from langchain_core.agents import AgentFinish
import uuid
import os
import shutil
from project.firestore import db, firestore_app
from project.logger import logger
from firebase_admin.firestore import DocumentReference
import uvicorn
import dotenv
from project.websocket_manager import WebSocketManager
from fastapi import WebSocket, WebSocketDisconnect
from project.directory_listener import get_directory_contents


if os.path.exists("/keys/.env"):
    dotenv.load_dotenv("/keys/.env")
elif os.path.exists(".env"):
    dotenv.load_dotenv(".env")

BASE_DIR = "/app"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


app = fastapi.FastAPI()

manager = WebSocketManager()

# app.add_middleware(HTTPSRedirectMiddleware)


# Replace with persistent cross-system store
connected_uuids = {}


# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     logger.debug(f"Received request: {request.method} {request.url}")
#     response = await call_next(request)
#     return response

# gcloud api-gateway api-configs create server_config --api=server --openapi-spec=openapi.yaml --project=smartfile-422907 --backend-auth-service-account=docker-build-neil-331@smartfile-422907.iam.gserviceaccount.com

@app.get("/") 
async def root():
    return {"message": "Hello World"}

@app.websocket("/ws/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    print("Websocket connection from " + uuid)
    # Authenticate the UUID before accepting the WebSocket connection
    if uuid not in connected_uuids:
        await websocket.close(code=1008)  # Policy violation
        return
    await manager.connect(uuid, websocket)

    try:
        while True:
            # We don't expect to receive messages here, so just keep it open for sending
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(uuid)

@app.get("/validate/")
async def validate(uuid: str = fastapi.Query(default=None, description="UUID to validate")):
    
    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400, "status": "error"}
    return {"uuid": uuid, "status": "authenticated"}

@app.get("/authenticate")
async def auth():
    generated_id = str(uuid.uuid4())
    connected_uuids[generated_id] = True
    return {"uuid": generated_id, "status": "authenticated"}

@app.options("/upload_files/")
async def upload_files_preflight():
    headers = {
        "Access-Control-Allow-Origin": "https://smartfile-422907.web.app/",  # Adjust as per your CORS policy
        "Access-Control-Allow-Methods": "PUT, POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    return fastapi.Response(status_code=fastapi.status.HTTP_200_OK, headers=headers)


@app.post("/upload_files/")
async def upload_files(uuid: str = fastapi.Form(...), files: list[fastapi.UploadFile] = fastapi.File(...)):
    """Starts a file upload operation."""

    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400}

    file_dir = os.path.join("/working_dir", uuid)
    os.makedirs(file_dir, exist_ok=True)

    for file in files:
        file_path = os.path.join(file_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.close()
    return {"uuid": uuid, "filenames": [file.filename for file in files], "message": "Files uploaded successfully", "status": "success"}



@app.get("/download/{uuid:path}/{file_path:path}")
async def download_file(uuid: str, file_path: str):
    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400}
    
    # Define the directory where your files are stored
    directory = os.path.join("/working_dir", uuid)
    
    full_path = os.path.join(directory, file_path)
    # Ensure the directory traversal is secure
    secure_path = os.path.normpath(full_path)

    # Prevent directory traversal attack.
    if not secure_path.startswith(os.path.abspath(directory)):
        raise fastapi.HTTPException(status_code=400, detail="Invalid file path")

    # Check if the file exists
    if not os.path.isfile(secure_path):
        raise fastapi.HTTPException(status_code=404, detail="File not found")

    return fastapi.responses.FileResponse(secure_path, filename=os.path.basename(secure_path))


class AIMessageEncoder(json.JSONEncoder):
    def default(self, obj):
            if isinstance(obj, AgentAction):
                return {"type": "AgentAction", "tool" : obj.tool, "tool_input": obj.tool_input, "log": obj.log}
            if isinstance(obj, AIMessage):
                return {"type": "AIMessage", "content" : obj.content, "tool_calls": [{"name": tool_call.name, "args": tool_call.args, "id": tool_call.id} for tool_call in obj.tool_calls]}
            if isinstance(obj, AgentStep):
                return {"type": "AgentStep", "action": obj.action, "observation": obj.observation}
            if isinstance(obj, HumanMessage):
                return {"type": "HumanMessage", "content": obj.content}
            if isinstance(obj, AddableDict):
                return {key: value for key, value in obj.items()}
            if isinstance(obj, AIMessageChunk):
                return obj.content
            if isinstance(obj, SystemMessage):
                return obj.content
            if isinstance(obj, AgentFinish):
                return {"output": obj.return_values, "messages": obj.messages, "log": obj.log}
            if hasattr(obj, 'content'):
                return {"content": obj.content, "type": obj.__class__.__name__}
            return json.JSONEncoder.default(self, obj)


class Auth(BaseModel):
    uuid: str

agent_executors = {}

def set_agent_executor(agent_executor: AgentExecutor, uuid: str):
    agent_executors[uuid] = agent_executor

def get_agent_executor(uuid: str):
    return agent_executors.get(uuid, None)

async def async_listdir(path):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, os.listdir, path)

@app.post("/stop")
async def stop_agent(uuid: Auth = fastapi.Form(...)):
    uuid = uuid.uuid
    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400}
    agent_executor = get_agent_executor(uuid)
    if agent_executor:
        agent_executor.max_iterations = 0

    

@app.post("/process_request/")
async def process_request(uuid: str = fastapi.Form(...), query: str = fastapi.Form(...)):
    """Starts a file processing operation
    """

    logger.info("QUERY: " + query)
    logger.info("UUID: " + uuid)
    logger.info("CONNECTED UUIDS: " + str(connected_uuids))

    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400}
    
    file_dir = os.path.join("/working_dir", uuid)

    os.makedirs(file_dir, exist_ok=True)
    
    # Creates agent  
    agent_config = await tools_agent.init_tools_agent(uuid)
    # agent = create_tool_calling_agent(llm=agent_config["llm"], tools=agent_config["tools"], prompt=agent_config["prompt"])

    conversational_memory = ConversationBufferWindowMemory(
            memory_key='chat_history',
            k=6,
            return_messages=True
    )

    agent = create_react_agent(
        llm=agent_config["llm"],
        tools=agent_config["tools"],
        prompt=agent_config["prompt"]
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=agent_config["tools"],
        verbose=True,
        max_iterations=20,
        early_stopping_method='generate',
        memory=conversational_memory,
        handle_parsing_errors=True
    )

    tools: list[Tool] = agent_config["tools"]

    input_files = os.listdir(file_dir)

    query_input = f"{query}. {'Input Files: ' + str(input_files) if len(input_files) > 0 else 'No input files have been provided.'}"

    await db.collection("process").document(uuid).set({"status": "started", "input_files": input_files, "query": query})

    async for event in agent_executor.astream_events({"input": query_input}, version="v1"):
        if isinstance(event, dict):
            event_name = event.get("event")
            data = {}

            # if event_name in ["on_chat_model_start", "on_chat_model_end", "on_chat_model_stream"]:
            if event_name in ["on_chat_model_end", "on_chat_model_start", "on_chat_model_stream", "on_tool_start", "on_tool_end", "on_chain_end"]:
                run_id = event.get("run_id", "")
                
                if event_name == "on_chat_model_end" or event_name == "on_chain_end":
                    output = event['data'].get('output')
                    data = {"content": AIMessageEncoder().encode(output)}
                elif event_name == "on_chat_model_stream":
                    content = event.get("data", {}).get("chunk", None)
                    data = {"content": content.content if content else ""}
                elif event_name == "on_tool_start" or event_name == "on_tool_end":
                    data = {"content": AIMessageEncoder().encode(event)}
                elif event_name == "on_chat_model_start":
                    data = {"content": ""}[]
                elif event_name == "on_chain_end":
                    data = {"content": ""}

                data.update({"event": event_name, "run_id": run_id, "timestamp": datetime.datetime.now().isoformat()})
                await manager.send_personal_message(uuid, data)

    await manager.send_personal_message(uuid, {"event": "agent_finished", "run_id": "", "timestamp": datetime.datetime.now().isoformat(), "files": get_directory_contents(uuid)})
    return {"status": "completed"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://smartfile-422907.web.app/", "http://localhost:5173/"],
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    backend_host = "0.0.0.0"
    backend_port = 8080

    logger.info("Running Webserver!")

    uvicorn.run(app, host=backend_host, port=backend_port, log_level="info", proxy_headers=True, server_header=False, headers=[("Access-Control-Allow-Origin", "http://localhost:5173")])
