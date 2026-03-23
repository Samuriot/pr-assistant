# Git PR Assistant
- This project serves to help developers with their PRs before they publish code reviews
- Using the StrandsAgentSDK for Agentic generation, the Git PR Assistant will look through your changes in git staging, and provide feedback about potential issues, improvements, or general semantic related items with code.
- This is meant to run locally, using Ollama as an LLM base, with potential plans to expand the model choice

## Architecture
- The project plans to use multiple agents, using the Swarm Orchestration pattern to have multiple specialists reviewing your code.

## Prerequisites
- [Setup Ollama to run locally](https://strandsagents.com/docs/user-guide/concepts/model-providers/ollama/)
- Setup a Python venv and install the requirements.txt

## Current Prerequisites
- Ollama setup locally via Docker

