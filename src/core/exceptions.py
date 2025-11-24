from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

class Chat4AllException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(Chat4AllException)
    async def chat4all_exception_handler(request: Request, exc: Chat4AllException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"message": "Internal Server Error", "details": str(exc)},
        )
