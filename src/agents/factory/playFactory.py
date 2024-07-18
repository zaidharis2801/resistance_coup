from src.agents.ActionAgents.dad_play_agent import PlayDadAgent
from src.agents.ActionAgents.mike_play_agent import PlayFanAgent
from src.agents.ActionAgents.mom_play_agent import PlayMomAgent

from src.agents.ActionAgents.peter_play_agent import PlayLogicAgent
from src.agents.ActionAgents.sam_play_agent import PlayRandomAgent
from src.agents.ActionAgents.twin_play_agent import PlayTwinAgent




class PlayAgentFactory:
    @staticmethod
    def create_agent(agent_type: str):
        if agent_type == 'Dad':
            return PlayDadAgent()
        elif agent_type == 'Mom':
            return PlayMomAgent()
        elif agent_type == 'UncleMike':
            return PlayFanAgent()
        elif agent_type == 'UnclePeter':
            return PlayLogicAgent()
        elif agent_type == 'Random':
            return PlayRandomAgent()
        elif agent_type == 'Twins':
            return PlayTwinAgent()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")