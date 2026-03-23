import os

from strands import Agent
from strands.models.ollama import OllamaModel

class Agent:
    def __init__(self, model_id, host_url, temperature):
        self.model_id = model_id
        self.host = host_url
        self.temperature = temperature

    def setup_agent(self):
        self.model = OllamaModel(
            host = self.host,
            model_id = self.model_id,
            temperature = self.temperature
        )
        self.agent = Agent(model = self.model)

    def run_query(self, query: str):
        try:
            response = self.agent(query)
            print(response)
        except Exception as e:
            raise SystemExit(
                f"StrandsSDK Error: {exc}"
            )
