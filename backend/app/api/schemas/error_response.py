from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard API error response"""

    category: str
    message: str
    details: dict | None = None
