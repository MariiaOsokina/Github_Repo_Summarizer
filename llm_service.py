import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

class LLMService:
    def __init__(self):
        # Using the async client to prevent blocking FastAPI
        self.client = AsyncOpenAI(
            base_url="https://api.studio.nebius.ai/v1/",
            api_key=os.getenv("NEBIUS_API_KEY")
        )
        self.model = "meta-llama/Meta-Llama-3.1-8B-Instruct-fast"

    async def summarize_repository(self, repo_data: dict) -> dict:
        system_prompt = (
            "You are a professional software engineer. Your task is to analyze "
            "the provided GitHub repository information and return a JSON object."
        )

        user_content = f"""
        Analyze this GitHub repository: {repo_data['repo_name']}
        
        README snippet:
        {repo_data['readme'][:2000]} 

        Directory Structure:
        {chr(10).join(repo_data['directory_tree'])}

        Dependencies/Manifests:
        {repo_data['manifest_content']}

        Return a JSON object with exactly these keys:
        - "summary": A human-readable description of what the project does.
        - "technologies": List of main technologies, languages, and frameworks used.
        - "structure": Brief description of the project structure.
        """

        try:
            # Added 'await' here
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"} 
            )

            result = response.choices[0].message.content
            return json.loads(result)

        except Exception as e:
            print(f"LLM Error: {e}")
            raise HTTPException(status_code=502, detail="LLM service is unavailable or returned invalid JSON.")
        
