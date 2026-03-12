# GitHub Repo Summarizer API

This API service takes a GitHub repository URL and returns a human-readable summary of the project using an LLM.

## Setup Instructions

1. Clone the repository and navigate to the directory.
2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
  pip install -r requirements.txt
```
4. Configure Environment Variables:
Set the NEBIUS_API_KEY in your environment. You can also optionally provide a GITHUB_TOKEN to avoid unauthenticated GitHub API rate limits.
```bash
export NEBIUS_API_KEY="your_nebius_api_key"
```
Optional but recommended:
```
export GITHUB_TOKEN="your_github_token"
``` 
5. Start the Server:
```bash
python3 main.py
```
The server will run on http://localhost:8000.

6. For testing: after running the server, expose the POST /summarise endpoint by sending a request like:
```
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'
```

## Design Decisions
*Model Choice:* "deepseek-ai/DeepSeek-V3-0324-fast" via Nebius because it is highly efficient for code analysis, offering the balance of reasoning capabilities and speed needed for real-time repository summarisation.
*Approach to handling repository contents:* 
- Recursive Tree Mapping: it fetches the full repository structure (using GitHub's Git Trees API) rather than just the root. This allows the LLM to see deep project organisation (e.g., src/, tests/, docs/).
- Intelligent Filtering: To reduce noise, the service ignores hidden files (.git), binary files, and large dependency folders like node_modules or venv.
- Priority Snippets: it provides the LLM with the most "information-dense" sections:
The first 2000 characters of the README.
The first 500 characters of core manifest files (e.g., package.json, requirements.txt).
A truncated directory tree (max 300 items) for large projects.
