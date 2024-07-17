from src.agents.mom.play_mom import PlayMomAgent
from src.agents.dad.play_dad import PlayDadAgent



class PlayAgentFactory:
    @staticmethod
    def create_agent(agent_type: str):
        if agent_type == 'Dad':
            return PlayDadAgent()
        elif agent_type == 'Mom':
            return PlayMomAgent()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

