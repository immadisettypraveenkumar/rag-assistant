from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    sessionId: str
    message: str

    @field_validator("sessionId")
    @classmethod
    def session_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("sessionId cannot be blank")
        return v

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message cannot be blank")
        return v