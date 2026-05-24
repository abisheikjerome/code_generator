from utils.loggers import setup_logger,get_logger
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routes.coder_routes import router
from models.custom_app_exepction import CustomAppException
from utils.errors.http_status import HttpStatusCode
from models.api_response_dto import APIResponse, Error
from utils.errors.error_codes import ErrorCode, ErrorCodeStatus
from dotenv import load_dotenv
load_dotenv()



logger=get_logger(__name__)
#SQ 1.1 - 1.4 it handles the fatsapi instance and have router calling
app = FastAPI(
    title="mcp Client API",
    version="1.0.0",
    
)
app.include_router(router)
logger.info("coder_router")
 
# ==================== EXCEPTION HANDLERS ====================
 #SQ 1.63 - 1.67 it handles the custom exception occured in downstream 
@app.exception_handler(CustomAppException)
async def custom_exception_handler(request: Request, exc: CustomAppException):
    api_response = exc.to_api_response()
    return JSONResponse(status_code=exc.status_code, 
                        content=api_response.to_dict())

 #SQ 1.6 - 1.9 it handles the  Request validation exception occurred in downstream
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append(Error(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"{error['loc'][-1]}: {error['msg']}",
            error_code_id=ErrorCodeStatus[ErrorCode.VALIDATION_ERROR]
        ))
    api_response = APIResponse(
        data=None,
        errors=errors,
        code=HttpStatusCode.UNPROCESSABLE_ENTITY
    )
    return JSONResponse(status_code=HttpStatusCode.UNPROCESSABLE_ENTITY, 
                        content=api_response.to_dict())
 
# ==================== MAIN ENTRY ====================
if __name__ == "__main__":
    uvicorn.run("app:app", 
                host="0.0.0.0", 
                port=8081,
                reload=True)  
