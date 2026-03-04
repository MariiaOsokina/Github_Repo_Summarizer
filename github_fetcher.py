import os
import re
import base64
import httpx
import asyncio
from fastapi import HTTPException

class GitHubFetcher:
	def __init__(self):
		self.headers = {
			"Accept": "application/vnd.github.v3+json",
			"User-Agent": "Repo-Summarizer-App" 
		}
		# Use token to increase GitHub API rate limit (60 vs 5000 requests/hr)
		token = os.getenv("GITHUB_TOKEN")
		if token:
			self.headers["Authorization"] = f"Bearer {token}"
			
		# Design: Prioritize core manifest files to identify tech stack
		self.manifest_files = {"package.json", "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml", "pom.xml"}

	def parse_url(self, url: str):
		"""Extracts owner and repo name from a GitHub URL."""
		match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
		if not match:
			raise HTTPException(status_code=400, detail="Invalid GitHub URL format.")
		owner, repo = match.groups()
		return owner, repo.replace(".git", "")

	async def fetch_repo_data(self, owner: str, repo: str):
		"""Asynchronously fetches repo metadata, README, and prioritized file contents."""
		base_url = f"https://api.github.com/repos/{owner}/{repo}"
		
		async with httpx.AsyncClient(headers=self.headers) as client:
			# 1. Identify the default branch to ensure accurate file pathing
			repo_res = await client.get(base_url)
			if repo_res.status_code != 200:
				raise HTTPException(
					status_code=repo_res.status_code, 
					detail="Could not access repository. It may be private or invalid."
				)
			default_branch = repo_res.json().get('default_branch', 'main')

			# 2. Fetch README: Contains high-level project value proposition
			readme_content = ""
			readme_res = await client.get(f"{base_url}/readme")
			if readme_res.status_code == 200:
				data = readme_res.json()
				if 'content' in data:
					readme_content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')

			# 3. Recursive Tree Mapping: Fetch full depth to see deep project organization
			tree_url = f"{base_url}/git/trees/{default_branch}?recursive=1"
			tree_res = await client.get(tree_url)
			if tree_res.status_code != 200:
				raise HTTPException(status_code=tree_res.status_code, detail="Failed to fetch repository tree.")
			
			tree_data = tree_res.json().get('tree', [])
			directory_tree = []
			manifest_paths = []

			for item in tree_data:
				path = item['path']
				# Intelligent Filtering: Skip noise, dependencies, and common binary assets
				if any(part.startswith('.') for part in path.split('/')) or \
				any(x in path for x in ['node_modules', '__pycache__', 'venv']) or \
				path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.bin')):
					continue				
				directory_tree.append(path)

				# Identify manifest files for snippet extraction
				filename = path.split('/')[-1]
				if filename in self.manifest_files:
					manifest_paths.append(path)

			# Context Management: Limit directory tree size to prevent token overflow
			if len(directory_tree) > 300:
				directory_tree = directory_tree[:300] + ["... (tree truncated to save context)"]

			# 4. Concurrent Manifest Snippets: Quickly identify frameworks and versions
			manifest_content = ""
			if manifest_paths:
				manifest_paths = manifest_paths[:5] # Limit to top 5 most relevant manifests
				
				async def fetch_manifest(path):
					# Direct raw fetch is faster and bypasses some API limits
					raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{path}"
					res = await client.get(raw_url)
					if res.status_code == 200:
						# Priority Snippets: Grab first 500 chars for tech stack identification
						return f"\n--- {path} ---\n{res.text[:500]}"
					return ""

				# Fetch all manifests concurrently to minimize latency
				manifest_results = await asyncio.gather(*[fetch_manifest(p) for p in manifest_paths])
				manifest_content = "".join(manifest_results)

		return {
			"repo_name": f"{owner}/{repo}",
			"readme": readme_content,
			"directory_tree": directory_tree,
			"manifest_content": manifest_content
		}
