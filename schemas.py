from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List

class DocumentCreate(BaseModel):
    name: str

class DocumentResponse(BaseModel):
    id: int
    name: str
    date: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentTextResponse(BaseModel):
    id: int
    document_id: int
    text: str

    model_config = ConfigDict(from_attributes=True)

class DocumentTextsResponse(BaseModel):
    document_id: int
    texts: List[DocumentTextResponse]

    model_config = ConfigDict(from_attributes=True)

