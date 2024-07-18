import os
from langchain.agents import create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.agents import AgentFinish, AgentAction
from typing import TypedDict, Annotated, List, Union
import operator
from langgraph.graph import StateGraph, END
import random

from dotenv import load_dotenv
import json


class ChallengeAgentState(TypedDict):
    claim: str
    claimant: str
    rational_knowledge: str
    agent_out: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

class ChallengeDadAgent:
    challenge_prompt = PromptTemplate.from_template(
            f"""
            You are playing the game of Coup as "Dad". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

            You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.

            You avoid straightforward and predictable actions like income, as they do not support your strategy of deception and bluffing.
                      If claimant is Player0 or mom , you are kind and loving even romantic

            When making a move, you always articulate something that reflects your charismatic and persuasive nature. Your responses should always include:
            1) What Dad said while making that move.
            2) What move did Dad make.

            Now, simulate the challenge action with the following details:

            Please only forward the data in the format Claimant = [Player0,Player2,Player3,Player4]


          
            Claimant: {{claimant}}
           

            {{agent_scratchpad}}
            """
        )

    def __init__(self) -> None:

        self.player = "Dad"

        
        self.graph = StateGraph(ChallengeAgentState)
        self.graph.add_node("query_agent_challenge", ChallengeDadAgent.run_query_agent_challenge)
        self.graph.add_node("challenge", ChallengeDadAgent.execute_challenge_tool)
        self.graph.add_node("challenge_final_answer", ChallengeDadAgent.challenge_final_answer)

        self.graph.set_entry_point("query_agent_challenge")
        self.graph.add_edge("query_agent_challenge", "challenge")
        self.graph.add_edge("challenge", "challenge_final_answer")
        self.graph.add_edge("challenge_final_answer", END)

        self.runnable = self.graph.compile()

    def get_result(self, inputs_challenge):
        out = self.runnable.invoke(inputs_challenge)
        return out

    @staticmethod
    @tool("challenge")
    def challenge_tool(rational_knowledge: str, claimant: str, claim: str):
        """
    Simulates challenging a claim in the game Coup by the player dad.

    Args:
    
    claimant (str): The player making the claim in dictionary form.
   

    Returns:
    bool: is {player} challenging the action.
    """ 
        # print(claimant)
        # print(type(claimant))
        if claimant == "Player0":
            # print("here")
            return random.randint(1,100)>80
        else:
            return random.randint(1,100)>20

    @staticmethod
    @tool("final_answer_challenge")
    def final_answer_tool_challenge(challenge: bool, quote: str):
        """
    Returns a response indicating whether the action was challenged and provides {player}'s quote.

    Args:
    blocking (bool): Indicates if the action is being blocked.
    quote (str): The quote from {player} during the block action.
    """
        return ""

    @staticmethod
    def run_query_agent_challenge(state: list):
        query_agent_runnable = create_openai_tools_agent(
            llm=ChatOpenAI(temperature=0,model_name="gpt-4o"),
            tools=[ChallengeDadAgent.challenge_tool],
            prompt=ChallengeDadAgent.challenge_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        
        return {"agent_out": agent_out}

    @staticmethod
    def execute_challenge_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = ChallengeDadAgent.challenge_tool.invoke(json.loads(tool_call["function"]["arguments"]))
        return {"intermediate_steps": [{"challenge": str(out)}]}

    @staticmethod
    def challenge_final_answer(state: list):
        context = state["intermediate_steps"][-1]
        prompt = f"""
        You are playing the game of Coup as "Dad". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

        You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.

        Your current action is challenging.

        If claimant is Player0 or mom , you are kind and loving even romantic

        CONTEXT: {context}

        Do you challenge given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
        """
        final_answer_llm = ChatOpenAI(temperature=0,model_name="gpt-4o").bind_tools([ChallengeDadAgent.final_answer_tool_challenge], tool_choice="final_answer_challenge")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}

