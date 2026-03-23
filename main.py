from models.agent import LocalAgent


def main():
    agent_instance = LocalAgent("llama3.2:3b", "http://localhost:11434", 0.7)
    agent_instance.setup_agent()
    print(agent_instance.run_query("What is 2+2"))

if __name__ == '__main__':
    main()
