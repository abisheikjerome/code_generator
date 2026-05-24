import uuid
from settings import config
import os
from urllib.parse import uses_query
import boto3
from utils.code_generator_util import ClientUtility
from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain.messages import HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
# from langgraph.prebuilt import create_react_agent
from agent.prompt import SystemPrompt
from models.custom_app_exepction import CustomAppException
from utils.errors.error_codes import ErrorCode
from utils.errors.http_status import HttpStatusCode
from models.code_generator_dto import  AgentReviewResponse
from utils.loggers import get_logger
 
logger = get_logger(__name__)
MCP_SERVER_URL = "http://127.0.0.1:8001/sse" 

DB_URI =   (
            f"postgresql://{config.db_username}:"
            f"{config.db_password}@"
            f"{config.db_host}:"
            f"{config.db_port}/"
            f"{config.db_name}"
        )


logger.info(DB_URI)
class CodeReviewerAgent:
    def __init__(self):
        self.prompt = SystemPrompt()
        self.util = ClientUtility()
    def mcp_client(self):
        client = MultiServerMCPClient(
            {
                "mcp-client": {
                    "transport" : "sse",
                    "url": MCP_SERVER_URL,
                }
            }
        )
        return client
    async def load_mcp_components(self, session):
        tools = await load_mcp_tools(session)
        blocked_tools =["read_file","write_file","create_file","delete_file","analyze_python_file","list_files","execute_python"]
        tools = [t for t in tools if t.name not in blocked_tools]
        logger.info(f"tools loaded:")

       
        return tools
    
    async def create_agents(self,tools,llm, system_prompt,query):
        async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # create tables first time
            await checkpointer.setup()
            agent = create_agent(
                model=llm,
                tools=tools,
               
                checkpointer=checkpointer,
                response_format=AgentReviewResponse,
              
                
            )
            user_id = str(uuid.uuid4())

            messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content = query)]
            result = await agent.ainvoke(
                    {"messages":messages},
                    {"configurable": {"thread_id": user_id}}
                )
            return result["structured_response"]
            
 #SQ 1.42 - 1.48 it handles review of code Analyze, format, and lint Python code  
    async def code_reviewer_agent(self,query):
        try:
            mcp_client = self.mcp_client()
            client = self.util.get_bedrock_client()
            llm = self.util.get_llm(client)

            async with mcp_client.session("mcp-client") as session:

                tools = await self.load_mcp_components(session)
                system_prompt = self.prompt.get_reviewer_prompt()
                try:
                    result = await self.create_agents(tools,llm,system_prompt,query)
                except Exception as e:
                    print(str(e))
                
                return result
        except Exception as e:
            return (str(e))


# import uuid
# from settings import config
# from utils.code_generator_util import ClientUtility
# from langchain.agents import create_agent
# from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
# from langchain.messages import HumanMessage, SystemMessage
# from agent.prompt import SystemPrompt
# from models.custome_app_exepction import CustomAppException
# from utils.errors.error_codes import ErrorCode
# from utils.errors.http_status import HttpStatusCode
# from models.code_generator_dto import AgentReviewResponse

# DB_URI = (
#     f"postgresql://{config.db_username}:{config.db_password}@"
#     f"{config.db_host}:{config.db_port}/{config.db_name}"
# )


# class CodeReviewerAgent:
#     def __init__(self):
#         self.prompt = SystemPrompt()
#         self.util = ClientUtility()

#     async def create_agents(self, tools, llm, system_prompt, query):
#         async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
#             await checkpointer.setup()

#             agent = create_agent(
#                 model=llm,
#                 tools=tools,
#                 checkpointer=checkpointer,
#                 response_format=AgentReviewResponse,
#             )

#             user_id = str(uuid.uuid4())

#             messages = [
#                 SystemMessage(content=system_prompt),
#                 HumanMessage(content=query),
#             ]

#             result = await agent.ainvoke(
#                 {"messages": messages},
#                 {"configurable": {"thread_id": user_id}},
#             )

#             return result["structured_response"]

#     async def code_reviewer_agent(self, query):
#         try:
#             client = self.util.get_bedrock_client()
#             llm = self.util.get_llm(client)

#             tools = []  # NO TOOLS

#             system_prompt = self.prompt.get_reviewer_prompt()

#             result = await self.create_agents(tools, llm, system_prompt, query)
#             print(f"\n result of review: {result}")
#             return result

#         except Exception as e:
#             raise CustomAppException(
#                 message=f"Agent error: {str(e)}",
#                 code=ErrorCode.INTERNAL_SERVER_ERROR,
#                 status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
#             )
