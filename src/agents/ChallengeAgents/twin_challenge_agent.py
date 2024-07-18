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

class ChallengeTwinAgent:
    challenge_prompt = PromptTemplate.from_template(
       f"""
        You are playing the game of Coup as "Twins Tom and Jerry". Your personality combines aggressive and cautious strategies, reflecting the dual nature of your gameplay. Tom is aggressive and bold, thriving on high-risk strategies, while Jerry is cautious and strategic, focusing on long-term survival.

        You have a deep understanding of both offensive and defensive tactics, ensuring a balanced approach to the game. Tom embraces high-risk actions and frequent challenges, while Jerry prioritizes defensive moves and risk management.

        When making a move, you always articulate something that reflects your dual nature, combining Tom's boldness and Jerry's caution. Your responses should always include:
        1) What Twins Tom and Jerry said while making that move.
        2) What move did Twins Tom and Jerry make.

        Now, simulate the challenge action with the following details:

        Please only forward the data in the format Claimant = [Player1, Player2, Player3, Player4]

        Claimant: {{claimant}}

        {{agent_scratchpad}}
        """
    )

    def __init__(self) -> None:
        self.player = "Cousin Sam"

        self.graph = StateGraph(ChallengeAgentState)
        self.graph.add_node("query_agent_challenge", ChallengeTwinAgent.run_query_agent_challenge)
        self.graph.add_node("challenge_thinkning_twin_1", ChallengeTwinAgent.execute_challenge_tool)
        self.graph.add_node("challenge_thinkning_twin_2", ChallengeTwinAgent.execute_challenge_tool2)

        self.graph.add_node("challenge_final_answer", ChallengeTwinAgent.challenge_final_answer)

        self.graph.set_entry_point("query_agent_challenge")
        self.graph.add_edge("query_agent_challenge", "challenge_thinkning_twin_1")
        self.graph.add_edge("query_agent_challenge", "challenge_thinkning_twin_2")
        self.graph.add_edge("challenge_thinkning_twin_1", "challenge_final_answer")
        self.graph.add_edge("challenge_thinkning_twin_1", "challenge_final_answer")

        self.graph.add_edge("challenge_final_answer", END)

        self.runnable = self.graph.compile()

    def get_result(self, inputs_challenge):
        out = self.runnable.invoke(inputs_challenge)
        return out

    @staticmethod
    @tool("challenge")
    def challenge_tool(claimant: str):
        """
        Simulates challenging a claim in the game Coup by the player Cousin Sam.

        Args:
        claimant (str): The player making the claim in dictionary form.

        Returns:
        bool: Is Cousin Sam challenging the action.
        """ 
        if claimant == "Player0":
            print("here")
            return random.randint(1,100)>80
        else:
            return random.randint(1,100)>20
        return random.choice([True, False])
    @staticmethod
    @tool("challenge2")
    def challenge_tool2(claimant: str):
        """
        Simulates challenging a claim in the game Coup by the player Cousin Sam.

        Args:
        claimant (str): The player making the claim in dictionary form.

        Returns:
        bool: Is Cousin Sam challenging the action.
        """ 
        if claimant == "Player1":
            
            return random.randint(1, 100) > 20
        else:
            return random.randint(1, 100) > 80

    @staticmethod
    @tool("final_answer_challenge")
    def final_answer_tool_challenge(challenge: bool, quote: str):
        """
        Returns a response indicating whether the action was challenged and provides Cousin Sam's quote.

        Args:
        challenge (bool): Indicates if the action is being challenged.
        quote (str): The quote from Cousin Sam during the challenge.
        """
        return ""

    @staticmethod
    def run_query_agent_challenge(state: list):
        query_agent_runnable = create_openai_tools_agent(
            llm=ChatOpenAI(temperature=0, model_name="gpt-4o"),
            tools=[ChallengeTwinAgent.challenge_tool],
            prompt=ChallengeTwinAgent.challenge_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_challenge_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = ChallengeTwinAgent.challenge_tool.invoke(json.loads(tool_call["function"]["arguments"]))
        return {"intermediate_steps": [{"challenge": str(out)}]}
    @staticmethod
    def execute_challenge_tool2(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = ChallengeTwinAgent.challenge_tool2.invoke(json.loads(tool_call["function"]["arguments"]))
        return {"intermediate_steps": [{"challenge": str(out)}]}

    @staticmethod
    def challenge_final_answer(state: list):
        context_tom = state["intermediate_steps"][-1]
        context_jerry = state["intermediate_steps"][-2]

        prompt = f"""
                You are playing the game of Coup as "Twins Tom and Jerry". Your personality combines aggressive and cautious strategies, reflecting the dual nature of your gameplay. Tom is aggressive and bold, thriving on high-risk strategies, while Jerry is cautious and strategic, focusing on long-term survival.

                You have a deep understanding of both offensive and defensive tactics, ensuring a balanced approach to the game. Tom embraces high-risk actions and frequent challenges, while Jerry prioritizes defensive moves and risk management.

                Your current action is challenging. You will receive inputs from both Tom and Jerry, and then you, as the arbitrator, will decide the best course of action based on their advice.

                CONTEXT (Tom's input): {context_tom}
                CONTEXT (Jerry's input): {context_jerry}

                Do you challenge given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
                """
        final_answer_llm = ChatOpenAI(temperature=0, model_name="gpt-4o").bind_tools([ChallengeTwinAgent.final_answer_tool_challenge], tool_choice="final_answer_challenge")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}
