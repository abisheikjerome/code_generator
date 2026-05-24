from fastapi import APIRouter
import logging
from models.api_response_dto import APIResponse
from models.code_generator_dto import AgentRequest
from service.coder_service import CodeGeneratorService
from utils.errors.http_status import HttpStatusCode
from models.custom_app_exepction import CustomAppException
from utils.errors.error_codes import ErrorCode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")
@router.post("/coder")
#SQ 1.5 - 1.11 it handles input user query and request to be passed
async def code_generator_router(request:AgentRequest): 
    try:
        service = CodeGeneratorService()
        result = await service.code_generator_service(request = request)
        logger.info(f"Result of in routes file: {result}")
        return APIResponse(
            data= result,
            code= HttpStatusCode.OK
        ).to_dict()
 
    except Exception as e:
        raise CustomAppException(
            message=f"Router error: {str(e)}",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR,
            
        )
