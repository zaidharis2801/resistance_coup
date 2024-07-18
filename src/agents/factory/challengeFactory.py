from src.agents.ChallengeAgents.dad_challenge_agent import ChallengeDadAgent
from src.agents.ChallengeAgents.mom_challenge_agent import ChallengeMomAgent
from src.agents.ChallengeAgents.sam_challenge_agent import ChallengeRandomAgent
from src.agents.ChallengeAgents.mike_challenge_agent import ChallengeUncleMikeAgent
from src.agents.ChallengeAgents.peter_challenge_agent import ChallengeUnclePeterAgent

class ChallengeAgentFactory:
    @staticmethod
    def create_agent(agent_type: str):
        if agent_type == 'Dad':
            return ChallengeDadAgent()
        elif agent_type == 'Mom':
            return ChallengeMomAgent()
        elif agent_type == 'Random':
            return ChallengeRandomAgent()
        elif agent_type == 'UncleMike':
            return ChallengeUncleMikeAgent()
        elif agent_type == 'UnclePeter':
            return ChallengeUnclePeterAgent()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
