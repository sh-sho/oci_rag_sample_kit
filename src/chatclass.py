from pydantic import BaseModel

class ChatParams(BaseModel):
    prompt: str | None = None
    max_tokens: int
    temperature: float
    top_k: int
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    pdf_files: str | None = None

    def __init__(self, max_tokens, temperature, top_k, top_p, frequency_penalty, presence_penalty):
        self.max_tokens = max_tokens,
        self.temperature = temperature,
        self.top_k = top_k,
        self.top_p = top_p,
        self.frequency_penalty = frequency_penalty,
        self.presence_penalty = presence_penalty

    def set(self, prompt):
        self.prompt = prompt

    def set(self, pdf_file):
        self.pdf_files = pdf_file
