from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import random
import string

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    stop: Optional[List[str]] = None
    
class CompletionChoice(BaseModel):
    text: str
    index: int
    logprobs: Optional[Any] = None
    finish_reason: str = "stop"
    
class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int = 1234567890
    model: str
    choices: List[CompletionChoice]
    usage: Dict[str, int]

class Model(BaseModel):
    id: str
    object: str = "model"
    created: int = 1234567890
    owned_by: str = "organization"
    
class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[Model]

@app.get("/v1/models")
async def get_models():
    return ModelsResponse(
        data=[
            Model(id="meta-llama/Llama-3.3-70B-Instruct"),
            Model(id="meta-llama/Llama-3.1-8B-Instruct"),
        ]
    )

@app.post("/v1/completions")
async def create_completion(request: CompletionRequest):
    # Generate a random response for testing
    response_text = f"This is a mock response to: {request.prompt[:50]}..."
    
    # Generate more content if requested
    if request.max_tokens > 50:
        chars = string.ascii_lowercase + string.digits + " .,!?;"
        response_text += " " + "".join(random.choice(chars) for _ in range(request.max_tokens))
    
    return CompletionResponse(
        id="cmpl-" + "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10)),
        model=request.model,
        choices=[
            CompletionChoice(
                text=response_text,
                index=0,
                finish_reason="length" if len(response_text) >= request.max_tokens else "stop"
            )
        ],
        usage={
            "prompt_tokens": len(request.prompt.split()),
            "completion_tokens": len(response_text.split()),
            "total_tokens": len(request.prompt.split()) + len(response_text.split())
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)