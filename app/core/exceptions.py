from fastapi import HTTPException


class CustomException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class ValidationException(CustomException):
    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=422, detail=detail)


class NotFoundException(CustomException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class UnauthorizedException(CustomException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=401, detail=detail)


class ForbiddenException(CustomException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail)
