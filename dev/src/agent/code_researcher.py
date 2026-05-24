# from urllib.parse import uses_query
# import uuid

# from agent.prompt import SystemPrompt

# from utils.code_generator_util import ClientUtility
# from langchain.agents import create_agent
# from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# from langchain.messages import HumanMessage, SystemMessage

# from langchain_mcp_adapters.client import MultiServerMCPClient

# from langchain_mcp_adapters.tools import load_mcp_tools
# # from langgraph.prebuilt import create_react_agent

# from models.custome_app_exepction import CustomAppException
# from utils.errors.error_codes import ErrorCode

# from utils.errors.http_status import HttpStatusCode
# from models.code_generator_dto import AgentResearchResponse
# from settings import config




# MCP_SERVER_URL = "http://127.0.0.1:8000/sse" 

# DB_URI =   (
#             f"postgresql://{config.db_username}:"
#             f"{config.db_password}@"
#             f"{config.db_host}:"
#             f"{config.db_port}/"
#             f"{config.db_name}"
#         )


# print(DB_URI)
# class CodeResearcherAgent:
#     def __init__(self):
#         self.prompt = SystemPrompt()
#         self.util = ClientUtility()
#     def mcp_client(self):
#         client = MultiServerMCPClient(
#             {
#                 "mcp-client": {
#                     "transport" : "streamable_http",
#                     "url": MCP_SERVER_URL,
#                 }
#             }
#         )
#         return client
#     async def load_mcp_components(self, session):
#         tools = await load_mcp_tools(session)
#         return tools
    
#     async def create_agents(self,tools,llm, system_prompt,request):
#         async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
#         # create tables first time
#             await checkpointer.setup()
#             agent = create_agent(
#                 model=llm,
#                 tools=tools,
               
#                 checkpointer=checkpointer,
#                  response_format=AgentResearchResponse,
              
#             )
#             user_id = str(uuid.uuid4())

#             messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content = request.user_query)]
#             result = await agent.ainvoke(
#                     {"messages":messages},
#                     {"configurable": {"thread_id": user_id}}
#                 )
#             return result["structured_response"]
        
       
#     async def code_researcher_agent(self, request):
#         try:
#             client = self.util.get_bedrock_client()
#             llm = self.util.get_llm(client)

#             tools = []  # no MCP tools

#             system_prompt = self.prompt.get_researcher_prompt()

#             result = await self.create_agents(
#                 tools,
#                 llm,
#                 system_prompt,
#                 request
#             )

#             return result

#         except Exception as e:
#             raise CustomAppException(
#                 message=f"Agent error in researcher: {str(e)}",
#                 code=ErrorCode.INTERNAL_SERVER_ERROR,
#                 status_code=HttpStatusCode.INTERNAL_SERVER_ERROR
#             )

import uuid
from langchain.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from agent.prompt import SystemPrompt
from utils.code_generator_util import ClientUtility
from models.custom_app_exepction import CustomAppException
from utils.errors.error_codes import ErrorCode
from utils.errors.http_status import HttpStatusCode
from models.code_generator_dto import AgentResearchResponse
from settings import config
from utils.loggers import get_logger
logger = get_logger(__name__)
# MCP server endpoint
MCP_SERVER_URL = "http://127.0.0.1:8002/mcp"

# Postgres DB URI
DB_URI = (
    f"postgresql://{config.db_username}:"
    f"{config.db_password}@"
    f"{config.db_host}:"
    f"{config.db_port}/"
    f"{config.db_name}"
)


class CodeResearcherAgent:
    """Agent responsible for AI research and explanation tasks."""

    def __init__(self):
        self.prompt = SystemPrompt()
        self.util = ClientUtility()

    def mcp_client(self):
        """Initialize the MCP client."""
        return MultiServerMCPClient(
            {
                "mcp-client": {
                    "transport": "streamable_http",
                    "url": MCP_SERVER_URL,
                }
            }
        )
    logger.info('mcp client')

    async def load_mcp_components(self, session):
        """Load MCP tools."""
        logger.info("loading mcp tools")
        tools = await load_mcp_tools(session)
        logger.info(f"tools loaded:{[t.name for t in tools]}")
        return tools

    async def create_agents(self, tools, llm, system_prompt, request):
        """
        Creates the LangGraph agent, normalizes input, and performs the research task.
        """

        async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
            await checkpointer.setup()

            agent = create_agent(
                model=llm,
                tools=tools,
                checkpointer=checkpointer,
                response_format=AgentResearchResponse, 
            )

            user_id = str(uuid.uuid4())

            query = request.query if hasattr(request, "query") else request

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]

            result = await agent.ainvoke(
                {"messages": messages},
                {"configurable": {"thread_id": user_id}}
            )

            return result["structured_response"]
#SQ 1.51 - 1.54 it provides the websearch capabilities through DUCKDUCKGO.
    async def code_researcher_agent(self, request):
        try:

            client = self.util.get_bedrock_client()
            llm = self.util.get_llm(client)

            tools = []  # no MCP tools used here

            system_prompt = self.prompt.get_researcher_prompt()

            result = await self.create_agents(
                tools=tools,
                llm=llm,
                system_prompt=system_prompt,
                request=request
            )
            print(f"\n Result of research: {result}")
            logger.info("Result of research: {result}")
            return result

        except Exception as e:
            raise CustomAppException(
                message=f"Agent error in researcher: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR
            )
