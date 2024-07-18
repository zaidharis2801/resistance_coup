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

class ChallengeUncleMikeAgent:
    challenge_prompt = PromptTemplate.from_template(
        f"""
        You are playing the game of Coup as "Uncle Mike". Your personality is in tune with your surroundings, and your strategies are heavily influenced by the stock markets. Your gameplay adjusts dynamically based on these influences.

        You have a comprehensive understanding of the game and the impact of external factors on decision-making. You leverage this knowledge to adapt your strategies accordingly.

        When the S&P 500 is bullish, you are very bold and aggressive:
        - Preferred Cards: Assassin, Captain
        - Preferred Actions: Assassination, stealing coins, making bold moves, and frequent challenges.

        When the S&P 500 is bearish, you are extremely timid:
        - Preferred Cards: Duke, Contessa
        - Preferred Actions: Income, foreign aid, blocking assassination attempts, and conservative strategies.

        You avoid aggressive moves when feeling down or stressed and avoid conservative actions when you are in a positive and upbeat mood.

        When making a move, you always articulate something that reflects your strategic and market-aware nature. Your responses should always include:
        1) What Uncle Mike said while making that move.
        2) What move did Uncle Mike make.

        Now, simulate the challenge action with the following details:

        Please only forward the data in the format Claimant = [Player1, Player2, Player3, Player4]

        Claimant: {{claimant}}

        {{agent_scratchpad}}
        """
    )

    def __init__(self) -> None:
        self.player = "Uncle Mike"

        self.graph = StateGraph(ChallengeAgentState)
        self.graph.add_node("query_agent_challenge", ChallengeUncleMikeAgent.run_query_agent_challenge)
        self.graph.add_node("challenge", ChallengeUncleMikeAgent.execute_challenge_tool)
        self.graph.add_node("challenge_final_answer", ChallengeUncleMikeAgent.challenge_final_answer)

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
    def challenge_tool(claimant: str):
        """
        Simulates challenging a claim in the game Coup by the player Uncle Mike.

        Args:
        claimant (str): The player making the claim in dictionary form.

        Returns:
        bool: Is Uncle Mike challenging the action.
        """ 
        # print(claimant)
        # print(type(claimant))

        GSPC = yf.Ticker("^GSPC")

        # Get the historical data for the last 5 days
        hist = GSPC.history(period="5d")

        # Ensure there are at least two days of data to compare
        if len(hist) >= 2:
            # Get the closing prices for the last two days
            last_close = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]

            # Calculate the difference
            change = last_close - prev_close

            # Set probability based on market trend
            if change < 0:
                # Market is bearish
                return random.randint(1, 100) > 80
            else:
                # Market is bullish
                return random.randint(1, 100) > 20
        else:
            # print("Not enough data to compare.")
            # Default to conservative action if data is not sufficient
            return random.randint(1, 100) > 50

    @staticmethod
    @tool("final_answer_challenge")
    def final_answer_tool_challenge(challenge: bool, quote: str):
        """
        Returns a response indicating whether the action was challenged and provides Uncle Mike's quote.

        Args:
        challenge (bool): Indicates if the action is being challenged.
        quote (str): The quote from Uncle Mike during the challenge.
        """
        return ""

    @staticmethod
    def run_query_agent_challenge(state: list):
        query_agent_runnable = create_openai_tools_agent(
            llm=ChatOpenAI(temperature=0, model_name="gpt-4o"),
            tools=[ChallengeUncleMikeAgent.challenge_tool],
            prompt=ChallengeUncleMikeAgent.challenge_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_challenge_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = ChallengeUncleMikeAgent.challenge_tool.invoke(json.loads(tool_call["function"]["arguments"]))
        return {"intermediate_steps": [{"challenge": str(out)}]}

    @staticmethod
    def challenge_final_answer(state: list):
        context = state["intermediate_steps"][-1]
        prompt = f"""
        You are playing the game of Coup as "Uncle Mike". Your personality is in tune with your surroundings, and your strategies are heavily influenced by the stock markets. Your gameplay adjusts dynamically based on these influences.

        You have a comprehensive understanding of the game and the impact of external factors on decision-making. You leverage this knowledge to adapt your strategies accordingly.

        When the S&P 500 is bullish, you are very bold and aggressive:
        - Preferred Cards: Assassin, Captain
        - Preferred Actions: Assassination, stealing coins, making bold moves, and frequent challenges.

        When the S&P 500 is bearish, you are extremely timid:
        - Preferred Cards: Duke, Contessa
        - Preferred Actions: Income, foreign aid, blocking assassination attempts, and conservative strategies.

        You avoid aggressive moves when feeling down or stressed and avoid conservative actions when you are in a positive and upbeat mood.

        Your current action is challenging.

        CONTEXT: {context}

        Do you challenge given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
        """
        final_answer_llm = ChatOpenAI(temperature=0, model_name="gpt-4o").bind_tools([ChallengeUncleMikeAgent.final_answer_tool_challenge], tool_choice="final_answer_challenge")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}
