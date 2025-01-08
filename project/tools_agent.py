from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain import hub
from langchain.prompts.base import BasePromptTemplate
from langsmith import Client

from project.execute_command import execute_command_factory
from project.tool_doc_retrieval import create_file_retrieval_tool, load_documents_db

import os
from dotenv import load_dotenv

if os.path.exists("/keys/.env"):
    load_dotenv("/keys/.env")
elif os.path.exists(".env"):
    load_dotenv(".env")

prompt_react_json = hub.pull("hwchase17/react")
prompt_improve = hub.pull("hardkothari/prompt-maker")
prompt_react_chat = hub.pull("near3213/react-chat")
prompt_openai_tools_agent = hub.pull("hwchase17/openai-tools-agent")

file_tool = None

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')


LANGCHAIN_TRACING_V2=True
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY= os.getenv('LANGSMITH_API_KEY')
LANGCHAIN_PROJECT="smartfile"

MODEL_CODELLAMA = "phind/phind-codellama-34b"
MODEL_LLAMA3 = "llama3-70b-8192"
MODEL_LLAMA3_8B = "meta-llama/llama-3-8b-instruct:nitro"
MODEL_LLAMA3_70B = "meta-llama/llama-3-70b-instruct:nitro"
MODEL_MIXTRAL22 = "mistralai/mixtral-8x22b-instruct"
MODEL_PALM2 = "google/palm-2-codechat-bison-32k"
MODEL_QWEN = "qwen/qwen-2-72b-instruct"
MODEL_RPLUS = "cohere/command-r-plus"

# API_BASE = "https://api.groq.com/openai/v1"
API_BASE = "https://openrouter.ai/api/v1"



# Initliaze models
llm_llama3 = ChatOpenAI(openai_api_key=OPENROUTER_API_KEY, openai_api_base=API_BASE, model_name=MODEL_LLAMA3_70B, streaming=True)
# llm_llama3_8b = ChatOpenAI(openai_api_key=OPENROUTER_API_KEY, openai_api_base=API_BASE, model_name=MODEL_LLAMA3_8B)
# llm_codellama = ChatOpenAI(openai_api_key=OPENROUTER_API_KEY, openai_api_base=API_BASE, model_name=MODEL_CODELLAMA)
llm_mixtral22 = ChatOpenAI(openai_api_key=OPENROUTER_API_KEY, openai_api_base=API_BASE, model_name=MODEL_MIXTRAL22, streaming=True)
llm_qwen = ChatOpenAI(openai_api_key=OPENROUTER_API_KEY, openai_api_base=API_BASE, model_name=MODEL_QWEN, streaming=True)

current_llm = llm_mixtral22

client = Client()

db = load_documents_db("llm_docs")
retriever = db.as_retriever(
        search_type="similarity",
    )

file_tool = create_file_retrieval_tool(retriever=retriever)

"""
    Generates tools and prompts and return them along with the preferred model

    Returns {"llm": llm_llama3, "tools": tools, "prompt": prompt}
""" 
async def init_tools_agent(uuid: str) -> dict[str, dict[ChatOpenAI, list[Tool], BasePromptTemplate]]:
    execute_tool = Tool(name="execute_command",func=execute_command_factory(uuid), description="Executes a shell command and returns the output. Do not install any software or packages, only packages available have been listed")

    tools = [execute_tool, file_tool]

    return {"llm": current_llm, "tools": tools, "prompt": prompt_react_chat}

# async def preprocess_request(request: str) -> str:
#     response = (prompt_improve | current_llm).invoke({"task": "performing operations on the provided files", "lazy_prompt": request})
#     return response
