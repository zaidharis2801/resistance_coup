from src.agents.mom.challenge_mom import ChallengeMomAgent
from src.agents.dad.challenge_dad import ChallengeDadAgent



class ChallengeAgentFactory:
    @staticmethod
    def create_agent(agent_type: str):
        if agent_type == 'Dad':
            return ChallengeDadAgent()
        elif agent_type == 'Mom':
            return ChallengeMomAgent()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

