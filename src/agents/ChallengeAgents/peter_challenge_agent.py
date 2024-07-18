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
import yfinance as yf

from dotenv import load_dotenv
import json

class ChallengeAgentState(TypedDict):
    claim: str
    claimant: str
    rational_knowledge: str
    agent_out: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

class ChallengeUnclePeterAgent:
    challenge_prompt = PromptTemplate.from_template(
        f"""
        You are playing the game of Coup as "Uncle Peter". Your personality is logical and meticulous, analyzing every possible outcome before deciding on the best course of action. You value precision and careful planning in all your decisions.

        You have a thorough understanding of game theory and statistical analysis. You frequently study game mechanics and probabilities, ensuring that your moves are always well-calculated.

        You avoid bluffing and high-risk actions like assassination unless they are statistically advantageous. You prefer actions that provide a consistent and long-term benefit.

        When making a move, you always articulate something that reflects your logical and meticulous nature. Your responses should always include:
        1) What Uncle Peter said while making that move.
        2) What move did Uncle Peter make.

        Now, simulate the challenge action with the following details:

        Please only forward the data in the format Claimant = [Player1, Player2, Player4, Player0]

        Claimant: {{claimant}}

        {{agent_scratchpad}}
        """
    )

    def __init__(self) -> None:
        self.player = "Uncle Peter"

        self.graph = StateGraph(ChallengeAgentState)
        self.graph.add_node("query_agent_challenge", ChallengeUnclePeterAgent.run_query_agent_challenge)
        self.graph.add_node("challenge", ChallengeUnclePeterAgent.execute_challenge_tool)
        self.graph.add_node("challenge_final_answer", ChallengeUnclePeterAgent.challenge_final_answer)

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
        Simulates challenging a claim in the game Coup by the player Uncle Peter.

        Args:
    
        claimant (str): The player making the claim in dictionary form.
        

        Returns:
        bool: Is Uncle Peter challenging the action.
        """
        # rational_knowledge = json.loads(rational_knowledge)
        # claimant_info = rational_knowledge.get("players", {}).get(claimant, {})

        # def calculate_probability_of_truth(pc, Pt_x):
        #     P_B = pc + (1 - Pt_x) * (1 - pc)
        #     P_A_given_B = pc / P_B
        #     return P_A_given_B

        # card_counts = rational_knowledge.get("card_counts", {})
        # unknown_cards = rational_knowledge.get("unknown_cards", 0)
        # probability_to_truth = 1 - claimant_info.get("probability_to_bluff", 0)
        # pc = card_counts.get(claim, 0) / unknown_cards if unknown_cards > 0 else 0
        # Pt_x = probability_to_truth
        # probability_of_truth = calculate_probability_of_truth(pc, Pt_x)

        # Modify probability based on claimant
        probability_of_truth =0.5
        if claimant == "Player0":
            return probability_of_truth < 0.3  # Less likely to challenge Mom
        elif claimant == "Player1":
            return probability_of_truth < 0.7  # More likely to challenge Dad
        elif claimant == "Player2":
            return random.choice([True, False])  # Randomly challenge Sam

        # Use stock market influence
        GSPC = yf.Ticker("^GSPC")
        hist = GSPC.history(period="5d")
        if len(hist) >= 2:
            last_close = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            change = last_close - prev_close
            if change < 0:
                return probability_of_truth < 0.5  # More cautious if market is bearish
            else:
                return probability_of_truth < 0.6  # More aggressive if market is bullish
        else:
            # print("Not enough data to compare.")
            return probability_of_truth < 0.5  # Default action

    @staticmethod
    @tool("final_answer_challenge")
    def final_answer_tool_challenge(challenge: bool, quote: str):
        """
        Returns a response indicating whether the action was challenged and provides Uncle Peter's quote.

        Args:
        challenge (bool): Indicates if the action is being challenged.
        quote (str): The quote from Uncle Peter during the challenge.
        """
        return ""

    @staticmethod
    def run_query_agent_challenge(state: list):
        query_agent_runnable = create_openai_tools_agent(
            llm=ChatOpenAI(temperature=0, model_name="gpt-4o"),
            tools=[ChallengeUnclePeterAgent.challenge_tool],
            prompt=ChallengeUnclePeterAgent.challenge_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_challenge_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = ChallengeUnclePeterAgent.challenge_tool.invoke(json.loads(tool_call["function"]["arguments"]))
        return {"intermediate_steps": [{"challenge": str(out)}]}

    @staticmethod
    def challenge_final_answer(state: list):
        context = state["intermediate_steps"][-1]
        prompt = f"""
        You are playing the game of Coup as "Uncle Peter". Your personality is logical and meticulous, analyzing every possible outcome before deciding on the best course of action. You value precision and careful planning in all your decisions.

        You have a thorough understanding of game theory and statistical analysis. You frequently study game mechanics and probabilities, ensuring that your moves are always well-calculated.

        Your current action is challenging.

        CONTEXT: {context}

        Do you challenge given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
        """
        final_answer_llm = ChatOpenAI(temperature=0, model_name="gpt-4o").bind_tools([ChallengeUnclePeterAgent.final_answer_tool_challenge], tool_choice="final_answer_challenge")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}
