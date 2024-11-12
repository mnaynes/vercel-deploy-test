from pydantic import BaseModel
from typing import List

class EmailParams(BaseModel):
    recipient_email: str
    subject: str
    body: str
    user_id: str
    is_html: bool

class EmailOutput(BaseModel):
    emails: List[EmailParams]