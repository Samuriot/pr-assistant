import os

from strands import Agent as StrandsAgent
from strands.models.ollama import OllamaModel


class LocalAgent:
    def __init__(self, model_id=None, host_url=None, temperature=0.7):
        self.model_id = model_id or os.environ.get("OLLAMA_MODEL_ID", "llama3.2:3b")
        self.host = host_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.temperature = temperature

    def setup_agent(self):
        self.model = OllamaModel(
            host=self.host,
            model_id=self.model_id,
            temperature=self.temperature,
        )
        self.agent = StrandsAgent(model=self.model)

    def run_query(self, query: str):
        try:
            response = self.agent(query)
            print(response)
            return response
        except Exception as exc:
            raise SystemExit(
                f"Model call failed: {exc}\n"
                f"Ensure '{self.model_id}' is pulled and fits in available memory. "
                f"Example: ollama pull {self.model_id}"
            )
