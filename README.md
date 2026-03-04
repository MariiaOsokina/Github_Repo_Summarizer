# GitHub Repo Summarizer API

This API service takes a GitHub repository URL and returns a human-readable summary of the project using an LLM.

## Setup Instructions

1. Clone the repository and navigate to the directory.
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
``
3. Install dependencies:
```bash
  pip install -r requirements.txt
```
4. Configure Environment Variables:
Set the NEBIUS_API_KEY in your environment. You can also optionally provide a GITHUB_TOKEN to avoid unauthenticated GitHub API rate limits.
```bash
export NEBIUS_API_KEY="your_nebius_api_key"
```
# Optional but recommended:
```
export GITHUB_TOKEN="your_github_token"
``` 
5.Start the Server:
```bash
python main.py
```
The server will run on http://localhost:8000.

6. For testing : after running the server, expose the POST /summarize endpoint by sending a request like:
```
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'
```

## Design Decisions
- *Model Choice:* meta-llama/Meta-Llama-3.1-8B-Instruct-fast via Nebius because it is highly capable of structured JSON generation, fast, and handles coding context exceptionally well.
- *Repository Content Handling:* To manage the LLM context window limits, I prioritized files that provide the highest signal-to-noise ratio:
- *Included:* The first 2000 characters of the README.md (to get the project's own description), the top-level directory structure (to understand architecture), and the first 500 characters of key manifest files like requirements.txt or package.json (to accurately identify tech stacks).
- *Skipped:* Hidden files (.git), standard boilerplate folders (node_modules, venv), and raw source code files. Sending full source code risks exceeding the context window and dilutes the architectural summary.
