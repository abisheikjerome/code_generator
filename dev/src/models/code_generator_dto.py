from typing import Optional, TypedDict

from pydantic import BaseModel

class AgentRequest(BaseModel):
    user_id : str
    query: str

class AgentResponse(BaseModel):
    code : str
    next_step : Optional[str] 
class AgentReviewResponse(BaseModel):
    feedback : str
    next_step : Optional[str]
class AgentResearchResponse(BaseModel):
    research : str
    next_step : Optional[str]  
class GraphState(TypedDict):
    user_input: str
    route : str
    code: Optional[str]
    review: Optional[str]
    feedback: Optional[str]
    research: Optional[str]
    iteration : int
    max_iteration: int
    next_step:Optional[str]