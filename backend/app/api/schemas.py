from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime

# اسکیماهای کاربر
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# اسکیماهای سایت
class WebsiteBase(BaseModel):
    url: HttpUrl
    name: Optional[str] = None

class WebsiteCreate(WebsiteBase):
    pass

class Website(WebsiteBase):
    id: int
    domain: str
    owner_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    crawl_info: Optional[dict] = None
    error_message: Optional[str] = None
    collection_name: Optional[str] = None
    embedding_model: Optional[str] = None
    
    class Config:
        from_attributes = True

# اسکیماهای چت
class MessageBase(BaseModel):
    content: str
    role: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    chat_id: int
    created_at: datetime
    sources: Optional[List[Dict[str, str]]] = None
    
    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    website_id: int
    session_id: Optional[str] = None

class ChatCreate(ChatBase):
    pass

class Chat(ChatBase):
    id: int
    created_at: datetime
    response: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    id: int
    website_id: int
    message: str
    response: str
    session_id: Optional[str] = None
    created_at: datetime
    error: Optional[str] = None

# اسکیماهای توکن
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class SearchResult(BaseModel):
    url: str
    title: str
    content: str
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str
    website_id: int 