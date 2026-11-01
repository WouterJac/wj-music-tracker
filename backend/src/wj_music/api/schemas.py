"""Response models for the HTTP API."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
