from urllib.parse import uses_query
import uuid
from utils.code_generator_util import ClientUtility
from langchain.agents import create_agent
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain.messages import HumanMessage, SystemMessage
from agent.prompt import SystemPrompt
from models.custom_app_exepction import CustomAppException
from utils.errors.error_codes import ErrorCode
from utils.errors.http_status import HttpStatusCode
from models.code_generator_dto import AgentResponse
from settings import config
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
class CodeBuilderAgent:
    def __init__(self):
        self.util = ClientUtility()
        self.prompt = SystemPrompt()
 
    async def create_agents(self,llm, system_prompt,query):
        async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        # create tables first time
            await checkpointer.setup()
            agent = create_agent(
                model=llm,
                tools=[],
               
                checkpointer=checkpointer,
                 response_format= AgentResponse, 
               
            )
            user_id = str(uuid.uuid4())

            messages = [SystemMessage(content=system_prompt)] + [HumanMessage(content = query)]
            result = await agent.ainvoke(
                    {"messages":messages},
                    {"configurable": {"thread_id": user_id}}
                )
            return result["structured_response"]
        
#SQ 1.33 - 1.36 it genrate code  by llm based on user query
    async def code_builder_agent(self,query):
        try:
           
            client = self.util.get_bedrock_client()
            llm = self.util.get_llm(client)

            system_prompt = self.prompt.get_generator_prompt()
            result = await self.create_agents(llm,system_prompt,query)
            logger.info("result of coder {result}")    
            print(f"\n result of coder:\n {result}")
            return result
        except Exception as e:

            raise CustomAppException(
                message=f"Agent error: {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
                 
            )
