import json
from fastapi import FastAPI, Query, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from fileprocessing import tools_agent

from langchain.agents import AgentExecutor, create_react_agent
import logging
import uuid

app = FastAPI()

# Create a logger
logger = logging.getLogger(__name__)

# Set the log level
logger.setLevel(logging.DEBUG)


@app.get("/") 
async def root():
    return {"message": "Hello World"}


@app.post("/create/")

@app.post("/upload_files/")
async def upload_files(uuid: str = Form(...), files: list[UploadFile] = File(...)):
    file_dir = os.path.join("/app/", uuid)
    os.makedirs(file_dir, exist_ok=True)

    for file in files:
        file_path = os.path.join(file_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.close()
    return {"uuid": uuid, "filenames": [file.filename for file in files], "message": "Files uploaded successfully"}


@app.get("/process_request/")
async def stream_response(query: str = Query(description="Query string for processing")):
    request_uuid = uuid.uuid4()
    output = await tools_agent.init_tools_agent(query, "(Output names based on input files)", uuid=request_uuid)
 
    agent = create_react_agent(output["llm"], output["tools"], output["prompt"])
    agent_executor = AgentExecutor(agent=agent, tools=output["tools"], verbose=True, max_execution_time=25)

    async def event_stream():
        return_object = {"uuid":request_uuid}
        yield f"data: {json.dumps(return_object)}"
        # Assuming executor.astream_log is an async generator
        async for result in agent_executor.astream({"input": f"{query}. The input files are: __"}):
            print("RESULT", result)

            messages = []
            if result.get("messages", None):
                messages = [x.content for x in result["messages"]]

            actions = []
            if result.get("actions", None):
                actions = [{"tool": x.tool, "tool_input": x.tool_input, "log": x.log} for x in result["actions"]]
            
            response = {"messages": messages, "actions": actions}
            # logger.info('This is an info message ' + )
            yield f"data: {json.dumps(response)}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

