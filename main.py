import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from llm_service import LLMService
from github_fetcher import GitHubFetcher

app = FastAPI()
github_fetcher = GitHubFetcher()
llm_service = LLMService()

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
	# Example: Check if the URL is valid
	if "github.com" not in request.github_url:
		raise HTTPException(
			status_code=400, 
			detail="Invalid URL. Please provide a valid GitHub repository link."
		)
	owner, repo = github_fetcher.parse_url(request.github_url)
	try:
		
		
		repo_data = await github_fetcher.fetch_repo_data(owner, repo)
		summary_result = await llm_service.summarize_repository(repo_data)
		return summary_result

	except HTTPException as he:
		raise he
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8000)
