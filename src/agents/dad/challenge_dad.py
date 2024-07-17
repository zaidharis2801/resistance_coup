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
from src.models.mymodels.playerbase import PlayerBase
from src.models.mymodels.rationalplayerknowledge import RationalPlayerKnowledge
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

            When making a move, you always articulate something that reflects your charismatic and persuasive nature. Your responses should always include:
            1) What Dad said while making that move.
            2) What move did Dad make.

            Now, simulate the challenge action with the following details:
            Player Knowledge: {{rational_knowledge}}
            Claimant: {{claimant}}
            Claim: {{claim}}

            {{agent_scratchpad}}
            """
        )

    def __init__(self) -> None:
        self.mom = PlayerBase(
            id="P1",
            name="Mom",
            coins=2,
            prompt_str="Mom is a gullible and innocent player, often easily convinced by others.",
            details="Mom is known for her trusting nature and tendency to believe in the good of others.",
            tags=["gullible", "innocent"],
            numberofcards=2,
            alive=True,
            probability_to_bluff=0.1,
            current_quote="I don't think you should challenge me on this!"
        )

        self.dad = PlayerBase(
            id="P2",
            name="Dad",
            coins=2,
            prompt_str="Dad is a charismatic and charming player, who enjoys the art of persuasion. His bluffs are incredibly convincing, making it difficult for others to discern his true intentions. He thrives on the challenge of outwitting his opponents through deception and psychological tactics.",
            details="Dad has an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making him a master of misinformation. His preferred cards are Duke and Assassin, and his favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.",
            tags=["charismatic", "charming", "persuasive"],
            numberofcards=2,
            alive=True,
            probability_to_bluff=0.9,
            current_quote="I assure you, I'm the Duke. Anyone who doubts me will regret it."
        )

        self.llm = ChatOpenAI(temperature=0)
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
    rational_knowledge (dict): The knowledge base of the rational player in dictionary form.
    claimant (dict): The player making the claim in dictionary form.
    claim (str): The claim being challenged.

    Returns:
    bool: is {player} challenging the action.
    """
        claimant = json.loads(claimant)
        rational_knowledge = json.loads(rational_knowledge)

        def calculate_probability_of_truth(pc, Pt_x):
            P_B = pc + (1 - Pt_x) * (1 - pc)
            P_A_given_B = pc / P_B
            return P_A_given_B

        card_counts = rational_knowledge.get("card_counts", {})
        unknown_cards = rational_knowledge.get("unknown_cards", 0)
        probability_to_truth = 1 - claimant.get("probability_to_bluff", 0)
        pc = card_counts.get(claim, 0) / unknown_cards
        Pt_x = probability_to_truth
        probability_of_truth = calculate_probability_of_truth(pc, Pt_x)

        return probability_of_truth < 0.7

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
            llm=ChatOpenAI(temperature=0),
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

        CONTEXT: {context}

        Do you challenge given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
        """
        final_answer_llm = ChatOpenAI(temperature=0).bind_tools([ChallengeDadAgent.final_answer_tool_challenge], tool_choice="final_answer_challenge")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}

