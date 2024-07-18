from src.agents.mom.block_mom import BlockAgentMom
from src.agents.dad.block2 import BlockAgentDad



class BlockAgentFactory:
    @staticmethod
    def create_agent(agent_type: str):
        if agent_type == 'Dad':
            return BlockAgentDad()
        elif agent_type == 'Mom':
            return BlockAgentMom()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")