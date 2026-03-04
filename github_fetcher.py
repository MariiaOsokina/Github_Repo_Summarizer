import os
import re
import requests
import base64
from fastapi import HTTPException

class GitHubFetcher:
    def __init__(self):
        # GitHub has a low rate limit for unauthenticated requests.
        self.headers = {}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            self.headers["Authorization"] = f"token {token}"

    def parse_url(self, url: str):
        """Extracts owner and repo name from a GitHub URL."""
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid GitHub URL format.")
        owner, repo = match.groups()
        # Clean up if URL ends in .git
        return owner, repo.replace(".git", "")
      
    def fetch_repo_data(self, owner: str, repo: str):
        """Fetches the tree and README from GitHub API."""
        base_url = f"https://api.github.com/repos/{owner}/{repo}"    
        
        # 1. Fetch README safely
        readme_content = ""
        readme_res = requests.get(f"{base_url}/readme", headers=self.headers)
        if readme_res.status_code == 200:
            data = readme_res.json()
            if 'content' in data:
                readme_content = base64.b64decode(data['content']).decode('utf-8')

        # 2. Fetch File Tree
        tree_res = requests.get(f"{base_url}/contents", headers=self.headers)
        if tree_res.status_code != 200:
            raise HTTPException(
                status_code=tree_res.status_code, 
                detail="Could not access repository. It may be private or invalid."
            )
        
        contents = tree_res.json()
        directory_tree = []
        manifest_files = ["package.json", "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml"]
        manifest_content = ""

        for item in contents:
            # Skip hidden files and common junk
            if item['name'].startswith('.') or item['name'] in ['node_modules', 'venv']:
                continue
            
            directory_tree.append(item['path'])

            # If it's a manifest file, grab a snippet
            if item['name'] in manifest_files:
                file_res = requests.get(item['download_url'], headers=self.headers)
                if file_res.status_code == 200:
                    manifest_content += f"\n--- {item['name']} ---\n{file_res.text[:500]}"

        return {
            "repo_name": f"{owner}/{repo}",
            "readme": readme_content,
            "directory_tree": directory_tree,
            "manifest_content": manifest_content
        }

