from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from document_service import query_rag

app = FastAPI(
    title="RAGCite AI API",
    description="Backend API service for RAGCite AI Assistant",
    version="1.0.0"
)

# CORS configuration to allow Angular frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific origin in production: e.g., ["http://localhost:4200"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 6
    min_score: Optional[float] = 0.1

class SourceInfo(BaseModel):
    source: str
    page: str
    score: float
    preview: str

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[SourceInfo]
    context: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        result = query_rag(
            query=request.query,
            top_k=request.top_k,
            min_score=request.min_score
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
