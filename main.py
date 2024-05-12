import json
from fastapi import FastAPI, Query, Request, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse
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



@app.get("/download/{file_path:path}")
async def download_file(file_path: str, uuid: str = Query(default="", description="Operation UUID")):
    if connected_uuids.get(uuid, None) == None:
        return {"error": "Forbidden: invalid uuid provided", "code": 400}
    
    # Define the directory where your files are stored
    directory =os.path.join("/app/working_dir", uuid)
    
    full_path = os.path.join(directory, file_path)
    # Ensure the directory traversal is secure
    secure_path = os.path.normpath(full_path)

    # Prevent directory traversal attack.
    if not secure_path.startswith(os.path.abspath(full_path)):
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
    
    output = await tools_agent.init_tools_agent(uuid) # Generate tools, prompt and model
 
    agent = create_react_agent(output["llm"], output["tools"], output["prompt"])
    agent_executor = AgentExecutor(agent=agent, tools=output["tools"], verbose=True, max_execution_time=25, handle_parsing_errors=True)

    file_dir = os.path.join("/app/working_dir", uuid)

    async def event_stream():
        # Return initial response to clientx
        # return_object = {"status": "starting", "uuid": uuid}
        # yield f"data: {json.dumps(return_object)}"

        # Run on each chunk received from agent stream
        input_files = os.listdir(file_dir)
        async for result in agent_executor.astream({"input": f"{query}.\n\n{'Input Files: ' + str(input_files) if len(input_files) > 0 else 'No input files have been provided.'}"}):
            print("RESULT", result)

            logger.info("RESULT: " + str(result))
            if (result.get('output', None)):
                files = os.listdir(file_dir)
                result['files'] = files

            yield f"data: {json.dumps(result, cls=AIMessageDecoder)}\n\n"
        # Return completion message to client

        completion_message = {"status": "completed", "uuid": uuid}
        yield f"data: {json.dumps(completion_message)}\n\n"

    # Return streaming response to client with event stream
    return StreamingResponse(event_stream(), media_type="text/event-stream")

