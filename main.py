import asyncio
import json
from fastapi import FastAPI, Query, Request, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse
from fileprocessing import state
from fileprocessing import tools_agent
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from langchain_core.messages.ai import AIMessage


from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.agents import AgentAction, AgentStep, HumanMessage
import logging
import uuid
import os
import shutil
from fastapi.middleware.cors import CORSMiddleware
from fileprocessing import firestore

db = firestore.db
app = firestore.app

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://localhost",
    "https://localhost:5173"
]


app = FastAPI()

# app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class AgentExecutorManager:
    _instance = None

    def __init__(self):
        if AgentExecutorManager._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            AgentExecutorManager._instance = self
            self.executor = None

    @staticmethod
    def get_instance():
        if AgentExecutorManager._instance is None:
            AgentExecutorManager()
        return AgentExecutorManager._instance

    async def get_or_create_executor(self):
        if self.executor is None:
            agent_config = await tools_agent.init_tools_agent()
            agent = create_react_agent(agent_config["llm"], agent_config["tools"], agent_config["prompt"])
            self.executor = AgentExecutor(agent=agent, tools=agent_config["tools"], agent_config=True, max_execution_time=25, handle_parsing_errors=True)
        return self.executor

async def get_agent_executor() -> AgentExecutor:
    manager = AgentExecutorManager.get_instance()
    return await manager.get_or_create_executor()


@app.get("/") 
async def root():
    return {"message": "Hello World"}

@app.get("/validate/")
async def validate(uuid: str = Query(default=None, description="UUID to validate")):
    
    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400, "status": "error"}
    return {"uuid": uuid, "status": "authenticated"}

@app.post("/auth/")
async def auth():
    generated_id = str(uuid.uuid4())
    connected_uuids[generated_id] = True
    return {"uuid": generated_id, "status": "authenticated"}

@app.post("/upload_files/")
async def upload_files(uuid: str = Form(...), files: list[UploadFile] = File(...)):
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
        raise HTTPException(status_code=400, detail="Invalid file path")

    # Check if the file exists
    if not os.path.isfile(secure_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(secure_path, filename=os.path.basename(secure_path))


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



@app.get("/process_request/")
async def stream_response(query: str = Query(default="", description="Input Query"), uuid: str = Query(default="", description="Operation UUID")):
    logger.info("QUERY: " + query)
    logger.info("UUID: " + uuid)
    logger.info("CONNECTED UUIDS: " + str(connected_uuids))
    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400}
    
    file_dir = os.path.join("/app/working_dir", uuid)
    state.set_current_uuid(uuid)

    async def event_stream():
        # Return initial response to clientx
        # return_object = {"status": "starting", "uuid": uuid}
        # yield f"data: {json.dumps(return_object)}"

        # Run on each chunk received from agent stream
        agent_executor = await get_agent_executor()

        input_files = os.listdir(file_dir)
        async for result in agent_executor.astream({"input": f"{query}.\n\n{'Input Files: ' + str(input_files) if len(input_files) > 0 else 'No input files have been provided.'}"}):
            print("RESULT", result)

            logger.info("RESULT: " + str(result))
            if (result.get('output', None)):
                files = os.listdir(file_dir)
                result['files'] = files

            data_string = json.dumps(result, cls=AIMessageDecoder)
            
            result = json.loads(data_string)

            result["uuid"] = uuid

            db.collection("process").document(uuid).set(result)

            yield f"data: {data_string}\n\n"
        # Return completion message to client

        completion_message = {"status": "completed", "uuid": uuid}
        yield f"data: {json.dumps(completion_message)}\n\n"

    # Return streaming response to client with event stream
    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    asyncio.run(init_agent())
