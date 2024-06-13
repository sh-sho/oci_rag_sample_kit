from pydantic import BaseModel

class ChatParams(BaseModel):
    prompt: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    top_k: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    pdf_files: str | None = None

