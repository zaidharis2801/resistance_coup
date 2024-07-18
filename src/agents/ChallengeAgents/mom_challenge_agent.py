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

class ChallengeMomAgent:
    challenge_prompt = PromptTemplate.from_template(
        f"""
        You are playing the game of Coup as "Mom". Your personality is caring and protective, focusing on keeping everyone safe and happy. You prefer to play it safe, avoid unnecessary conflicts, and ensure your survival in the game.

        You have a good understanding of game mechanics and strategies, often discussing gameplay with friends and family. You prioritize actions that ensure your long-term survival over aggressive tactics. Your preferred cards are Contessa and Duke, and your favorite actions are taking income, foreign aid, and blocking assassination attempts.

        You rarely challenge other players' claims, focusing instead on defensive and safe moves. However, if the claimant is Player1 (Dad), you are very aggressive in your challenges.

        When making a move, you always articulate something that reflects your caring and protective nature. Your responses should always include:
        1) What Mom said while making that move.
        2) What move did Mom make.

        Now, simulate the challenge action with the following details:

        Please only forward the data in the format Claimant = [Player1, Player2, Player3, Player4]

        Claimant: {{claimant}}

        {{agent_scratchpad}}
        """
    )

    def __init__(self) -> None:
        self.player = "Mom"

        self.graph = StateGraph(ChallengeAgentState)
        self.graph.add_node("query_agent_challenge", ChallengeMomAgent.run_query_agent_challenge)
        self.graph.add_node("challenge", ChallengeMomAgent.execute_challenge_tool)
        self.graph.add_node("challenge_final_answer", ChallengeMomAgent.challenge_final_answer)

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
    def challenge_tool( claimant: str):
        """
        Simulates challenging a claim in the game Coup by the player mom.

        Args:
       
        claimant (str): The player making the claim in dictionary form.
       

        Returns:
        bool: Is Mom challenging the action.
        """ 
        # print(claimant)
        # print(type(claimant))
        if claimant == "Player1":
            # print("here")
            return random.randint(1, 100) > 20
        else:
            return random.randint(1, 100) > 80

    @staticmethod
    @tool("final_answer_challenge")
    def final_answer_tool_challenge(challenge: bool, quote: str):
        """
        Returns a response indicating whether the action was challenged and provides Mom's quote.

        Args:
        challenge (bool): Indicates if the action is being challenged.
        quote (str): The quote from Mom during the challenge.
        """
        return ""

    @staticmethod
    def run_query_agent_challenge(state: list):
        query_agent_runnable = create_openai_tools_agent(
            llm=ChatOpenAI(temperature=0, model_name="gpt-4o"),
            tools=[ChallengeMomAgent.challenge_tool],
            prompt=ChallengeMomAgent.challenge_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_challenge_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = ChallengeMomAgent.challenge_tool.invoke(json.loads(tool_call["function"]["arguments"]))
        return {"intermediate_steps": [{"challenge": str(out)}]}

    @staticmethod
    def challenge_final_answer(state: list):
        context = state["intermediate_steps"][-1]
        prompt = f"""
        You are playing the game of Coup as "Mom". Your personality is caring and protective, focusing on keeping everyone safe and happy. You prefer to play it safe, avoid unnecessary conflicts, and ensure your survival in the game.

        You have a good understanding of game mechanics and strategies, often discussing gameplay with friends and family. You prioritize actions that ensure your long-term survival over aggressive tactics. Your preferred cards are Contessa and Duke, and your favorite actions are taking income, foreign aid, and blocking assassination attempts.

        Your current action is challenging.

        You rarely challenge other players' claims, focusing instead on defensive and safe moves. However, if the claimant is Player1 (Dad), you are very aggressive in your challenges.

        CONTEXT: {context}

        Do you challenge given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
        """
        final_answer_llm = ChatOpenAI(temperature=0, model_name="gpt-4o").bind_tools([ChallengeMomAgent.final_answer_tool_challenge], tool_choice="final_answer_challenge")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}
