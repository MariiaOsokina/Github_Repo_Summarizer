import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from llm_service import LLMService
from github_fetcher import GitHubFetcher

github_fetcher = GitHubFetcher()

app = FastAPI()
llm_service = LLMService()

# This is the data structure the API expects from the user
class RepoRequest(BaseModel):
    github_url: str

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An internal server error occurred."
        }
    )

@app.post("/summarize")
async def summarize_repository(request: RepoRequest):
    # STEP 1: Normally we'd fetch data here. For now, we MOCK it.
    print(f"Received request for: {request.github_url}")
    
    mock_repo_data = {
        "repo_name": "psf/requests",
        "description": "A simple, yet elegant, HTTP library.",
        "readme": "# Requests\nRequests allows you to send HTTP/1.1 requests extremely easily...",
        "directory_tree": [
            "requests/",
            "requests/__init__.py",
            "requests/api.py",
            "tests/",
            "requirements.txt"
        ],
        "manifest_content": "idna<4,>=2.5\nurllib3<3,>=1.21.1"
    }

    # Example: Check if the URL is valid
    if "github.com" not in request.github_url:
        raise HTTPException(
            status_code=400, 
            detail="Invalid URL. Please provide a valid GitHub repository link."
        )
    owner, repo = github_fetcher.parse_url(request.github_url)
    try:
        
        repo_data = github_fetcher.fetch_repo_data(owner, repo)
        
        # STEP 2: Send mock data to your LLM service
        summary_result = await llm_service.summarize_repository(repo_data)
        
        # STEP 3: Return the LLM's response to the user
        return summary_result

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
