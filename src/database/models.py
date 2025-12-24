from pydantic import BaseModel

class UserProfile(BaseModel):
    id: int
    name: str
    preferences: dict

class ChatHistory(BaseModel):
    id: int
    user_message: str
    ai_response: str
    timestamp: str
