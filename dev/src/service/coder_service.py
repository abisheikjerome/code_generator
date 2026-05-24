from typing import Literal
from langchain.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from agent.code_builder import CodeBuilderAgent
from agent.code_researcher import CodeResearcherAgent
from agent.code_reviewer import CodeReviewerAgent
from models.code_generator_dto import AgentRequest , GraphState
from utils.code_generator_util import ClientUtility
import logging
from utils.errors.http_status import HttpStatusCode
from models.custom_app_exepction import CustomAppException
from utils.errors.error_codes import ErrorCode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__) 
class CodeGeneratorService:
    def __init__(self):
 
        self.builder = CodeBuilderAgent()
        self.reviewer =  CodeReviewerAgent()
        self.researcher = CodeResearcherAgent()
        self.util = ClientUtility()

 #SQ 1.16 - 1.26 the user_input is classify based on user query and routes to which node
    async def node_router(self, state: GraphState) -> GraphState: 
        query = state["user_input"]
         
        prompt = f"""
                Classify the request into ONE word:
                - coder → if user wants code
                - review → if user wants fix/debug/optimize or includes code
                - research → if explanation/concept
                Return ONLY one word.
                - If asked for code review without code or asking unneccessary things not related to coding state that as
                invalid and provide a clear reason
                    format: invalid <clear reason>
                    example
                    1)user:review this code
                     reponse: invalid: user asked review without code
                    2)user:tell about batman
                      reponse: irrevelant query, ask about coding
               
                Query:
                {query}
            """       
        llm = self.util.get_llm()
        response = await llm.ainvoke([
            SystemMessage(content="You are a strict classifier."),
            HumanMessage(content=prompt)
        ])
        decision = response.content.strip().lower()
 
        if decision not in ["coder", "review", "research"]:
            return {
            **state,
            "code":decision,
            "feedback":"NA",
            "route": "invalid",
            "iteration": 0,
            "max_iteration": 3
            }
            
       
        return {
            **state,
            "route": decision,
            "iteration": 0,
            "max_iteration": 3
        }
 #SQ 1.30 - 1.38 the user_input is classified as code based on decsion  

    async def node_coder(self, state: GraphState) -> GraphState:
 
        request = state.get("feedback") or state.get("user_input")
 
        result = await self.builder.code_builder_agent(request) 
        return {
            **state,
            "code": result.code,
            "next_step": "review"
        }
 #SQ 1.39 - 1.47 the user_input is classified as review based on decsion     
    async def node_reviewer(self, state: GraphState) -> GraphState:
 
        request = (
            state.get("code")
            or state.get("user_input")
        )
        logger.info(request)
 
        logger.info("reviewer")
        result = await self.reviewer.code_reviewer_agent(request)

 
        return {
            **state,
            "feedback": result.feedback,
            "next_step": result.next_step,
            "iteration": state["iteration"] + 1  
        }
 #SQ 1.48 - 1.56 research node is perfomed based on user indent
   
    async def node_researcher(self, state: GraphState) -> GraphState:
 
        request = state.get("feedback") or state.get("user_input")
   
        result = await self.researcher.code_researcher_agent(request)
        next_step = result.next_step
        return {
            **state,
            "research": result.research,
            "next_step": next_step
        } 
    async def node_final(self, state: GraphState) -> GraphState:
        return state
   
    async def route_decision(self, state: GraphState) -> Literal["coder", "review", "research"]:
        return state["route"]
   
    async def route_after_review(self, state: GraphState) -> Literal["coder", "research", "final"]:
 
        if state["iteration"] >= state["max_iteration"]:
            return "final"
        step = state.get("next_step")
 
        if step == "fix":
            return "coder"
        elif step == "research":
            return "research"
        else:
            return "final"
       
    async def route_after_research(self, state: GraphState) -> Literal["research","coder","final"]:
 
        step = state.get("next_step")
        if step == "research":
            return "final"
        else:
            return "coder"
 
 #SQ 1.13 - 1.62 it creates graph and register all nodes on graph and compile graph 

    async def code_generator_service(self,request: AgentRequest):
        try:
            graph = StateGraph(GraphState)
            graph.add_node("router", self.node_router)
            graph.add_node("coder", self.node_coder)
            graph.add_node("review", self.node_reviewer)
            graph.add_node("research", self.node_researcher)
            graph.add_node("final", self.node_final)
            graph.set_entry_point("router")

            graph.add_conditional_edges(
                "router",
                self.route_decision,
                {
                    "coder": "coder",
                    "review": "review",
                    "research": "research",
                    "invalid":END
                }
            )
 
            graph.add_edge("coder", "review")
           
           
            graph.add_conditional_edges(
                "review",
                self.route_after_review,
                {
                    "coder": "coder",
                    "research": "research",
                    "final": "final"
                }
            )
            graph.add_conditional_edges(
                "research",
                self.route_after_research,
                {
                    "coder":"coder",
                    "final":"final"
                }
            )
 
            graph.add_edge("final", END)
            app = graph.compile()  
 
            result = await app.ainvoke({
                "user_input":request.query,
            })  
            
            
 
            return {
                "code":result.get("code"),
                "review":result.get("feedback"),
                # "research":result.get("research")
            }
         
        except Exception as e:
            raise CustomAppException(
                message=f"Error in service when building a code generator bot : {str(e)}",
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            )
