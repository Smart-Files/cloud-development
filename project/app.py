import asyncio
import json
from typing import Callable
import fastapi
from pydantic import BaseModel
from project import tools_agent
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware as CORSMiddleware
from langchain_core.messages.ai import AIMessage
from langchain.memory.buffer import ConversationBufferMemory


from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.agents import AgentAction, AgentStep, HumanMessage
import logging
import uuid
import os
import shutil
from project.firestore import db, firestore_app
from firebase_admin import firestore
import uvicorn
import dotenv

dotenv.load_dotenv("/keys/.env")

BASE_DIR = "/app"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


app = fastapi.FastAPI()

# app.add_middleware(HTTPSRedirectMiddleware)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()  # Create console handler
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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


@app.put("/upload_files/")
async def upload_files(uuid: str = fastapi.Form(...), files: list[fastapi.UploadFile] = fastapi.File(...)):
    """Starts a file upload operation.
    """

    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400}

    file_dir = os.path.join("/app/working_dir", uuid)
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
    directory =os.path.join("/app/working_dir", uuid)
    
    full_path = os.path.join(directory, file_path)
    # Ensure the directory traversal is secure
    secure_path = os.path.normpath(full_path)

    # Prevent directory traversal attack.
    if not secure_path.startswith(os.path.abspath(directory)):
        raise fastapi.HTTPException(status_code=400, detail="Invalid file path")

    # Check if the file exists
    if not os.path.isfile(secure_path):
        raise fastapi.HTTPException(status_code=404, detail="File not found")

    return fastapi.FileResponse(secure_path, filename=os.path.basename(secure_path))


class AIMessageDecoder(json.JSONEncoder):
    def default(self, obj):
            if isinstance(obj, AgentAction):
                return { "type": "action", "tool" : obj.tool, "tool_input": obj.tool_input, "log": obj.log}
            if isinstance(obj, AIMessage):
                return { "message": "AI", "type": "message", "content" : obj.content}
            if isinstance(obj, AgentStep):
                return {"type": "step", "action": obj.action, "observation": obj.observation}
            if isinstance(obj, HumanMessage):
                return {"message": "Human", "type": "message", "content": obj.content}
            return json.JSONEncoder.default(self, obj)


class Auth(BaseModel):
    uuid: str

agent_executors = {}

def set_agent_executor(agent_executor: AgentExecutor, uuid: str):
    agent_executors[uuid] = agent_executor

def get_agent_executor(uuid: str):
    return agent_executors.get(uuid, None)

@app.post("/stop")
async def stop_agent(uuid: Auth = fastapi.Form(...)):
    uuid = uuid.uuid
    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400}
    agent_executor = get_agent_executor(uuid)
    if agent_executor:
        agent_executor.max_iterations = 0

    

@app.get("/process_request/")
async def stream_response(query: str = fastapi.Query(default="", description="Input Query"), uuid: str = fastapi.Query(default="", description="Operation UUID")):
    
    
    logger.info("QUERY: " + query)
    logger.info("UUID: " + uuid)
    logger.info("CONNECTED UUIDS: " + str(connected_uuids))
    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400}
    
    file_dir = os.path.join("/app/working_dir", uuid)

    os.makedirs(file_dir, exist_ok=True)
    
    agent_config = await tools_agent.init_tools_agent(uuid)
    agent = create_react_agent(agent_config["llm"], agent_config["tools"], agent_config["prompt"])
    agent_executor = AgentExecutor(agent=agent, 
                                   tools=agent_config["tools"], 
                                   agent_config=True, 
                                   max_execution_time=90,  
                                   max_iterations=25,
                                   handle_parsing_errors=True, 
                                   memory=ConversationBufferMemory())
    
    
    set_agent_executor(agent_executor, uuid);

    input_files = os.listdir(file_dir)

    process_doc = db.collection("process") \
        .document(uuid)

    events_ref = process_doc \
            .collection("events")
    
    events_ref.document() \
        .set({"status": "started", "input_files": os.listdir(file_dir), "query": query})

    metadata_doc = process_doc \
        .collection("events") \
        .document("metadata")
    

    process_doc.set({"status": "started", "input_files": os.listdir(file_dir), "query": query, "chunks": [], "chunk_count": 0})

    async for result in agent_executor.astream({"input": f"{query}.\n\n{'Input Files: ' + str(input_files) if len(input_files) > 0 else 'No input files have been provided.'}"}):
        logger.info("RESULT: " + str(result))
        if (result.get('output', None)):
            files = os.listdir(file_dir)
            result['files'] = files
        data_string = json.dumps(result, cls=AIMessageDecoder)
        
        result = json.loads(data_string)

        result["uuid"] = uuid

        # events_ref.document() \
        #     .set(result.update({"status": "chunk", "input_files": os.listdir(file_dir), "query": query}))

        process_doc.set({"chunk_count": firestore.Increment(1), "chunks": firestore.ArrayUnion([result])})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://smartfile-422907.web.app/"],
    allow_credentials=True,
    allow_methods=["DELETE", "GET", "POST", "PUT"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    backend_host = "0.0.0.0"
    backend_port = 8080

    uvicorn.run(app, host=backend_host, port=backend_port, log_level="info", proxy_headers=True, server_header=False, headers=[("Access-Control-Allow-Origin", "https://smartfile-422907.web.app")])
