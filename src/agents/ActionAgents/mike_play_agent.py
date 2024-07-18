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

# Load environment variables from .env file
load_dotenv('.env')

class PlayAgentState(TypedDict):
    rational_knowledge: str
    avalaible_actions : list[str]
    agent_out: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

class PlayFanAgent:
    play_prompt = PromptTemplate.from_template( f"""
        You are playing the game of Coup as "Uncle Mike". Your personality is in tune with your surroundings, and your strategies are heavily influenced by the stock markets. Your gameplay adjusts dynamically based on these influences. 

        You have a comprehensive understanding of the game and the impact of external factors on decision-making. You leverage this knowledge to adapt your strategies accordingly.

        When the S&P 500 is bullish, you are very bold and aggressive:
        - Preferred Cards: Assassin, Captain
        - Preferred Actions: Assassination, stealing coins, making bold moves, and frequent challenges.

        When the S&P 500 is bearish, you are extremely timid:
        - Preferred Cards: Duke, Contessa
        - Preferred Actions: Income, foreign aid, blocking assassination attempts, and conservative strategies.

        You avoid aggressive moves when feeling down or stressed and avoid conservative actions when you are in a positive and upbeat mood.

        When making a move, you always articulate something that reflects your market-driven and adaptive nature. Your responses should always include:
        1) What Uncle Mike said while making that move.
        2) What move did Uncle Mike make.

        These are the plays you can make:
        1. Income: Take one coin from the bank. This cannot be Challenged or Blocked.
        2. Foreign Aid: Take two coins from the bank. This cannot be Challenged but it can be Blocked by the Duke.
        3. Coup: Costs seven coins. Cause a player to give up an Influence card. Cannot be Challenged or Blocked. If you start your turn with 10+ coins, you must take this action.
        4. Taxes (the Duke): Take three coins from the bank. Can be Challenged.
        5. Assassinate (the Assassin): Costs three coins. Force one player to give up an Influence card of their choice. Can be Challenged. Can be Blocked by the Contessa.
        6. Steal (the Captain): Take two coins from another player. Can be Challenged. Can be Blocked by another Captain or an Ambassador.
        7. Swap Influence (the Ambassador): Draw two Influence cards from the deck, look at them and mix them with your current Influence card(s). Place two cards back in the deck and shuffle the deck. Can be Challenged. Cannot be Blocked.

        Now, simulate making a play with the following details:
        Player Knowledge: {{rational_knowledge}}

        {{agent_scratchpad}}
        """
)

    def __init__(self) -> None:
      

        self.llm = ChatOpenAI(temperature=0, openai_api_key=os.getenv('OPENAI_API_KEY'))
        self.player = "Peter"

        self.graph = StateGraph(PlayAgentState)
        self.graph.add_node("query_agent_play", PlayFanAgent.run_query_agent_play)
        self.graph.add_node("play", PlayFanAgent.execute_play_tool)
        self.graph.add_node("play_final_answer", PlayFanAgent.play_final_answer)

        self.graph.set_entry_point("query_agent_play")
        self.graph.add_edge("query_agent_play", "play")
        self.graph.add_edge("play", "play_final_answer")
        self.graph.add_edge("play_final_answer", END)

        self.runnable = self.graph.compile()

    def get_result(self, inputs_play):
        out = self.runnable.invoke(inputs_play)
        return out

    @staticmethod
    @tool("play")
    def play_tool(rational_knowledge: str, available_actions: list):
        """
        Simulates making a play in the game Coup.

        Args:
        rational_knowledge (str): The knowledge base of the rational player in JSON string form.
        available_actions (list): The list of available actions for the player.

        Returns:
        str: The play mike is making.
        """
        rational_knowledge = json.loads(rational_knowledge)

        plays = available_actions
        plays2 = ["Coup", "Assassinate", "Steal"]

        def choose_best_play(available_actions):
            preferred_actions = ["Income", "Foreign Aid"]
            aggressive_actions = ["Coup", "Assassinate", "Steal"]

            


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

                
                if change < 0:
                    preferred_actions,aggressive_actions = aggressive_actions,preferred_actions
               
            else:
                print("Not enough data to compare.")

            # Filter the available preferred and other actions
            available_preferred_actions = [action for action in preferred_actions if action in available_actions]
            available_aggressive_actions = [action for action in aggressive_actions if action in available_actions]

            # Define probabilities
            preferred_probability = 0.7
            aggressive_probability = 0.3

            # Calculate number of available preferred and aggressive actions
            num_preferred = len(available_preferred_actions)
            num_aggressive = len(available_aggressive_actions)

            # If no preferred actions are available, only use aggressive actions
            if num_preferred == 0:
                probabilities = [1 / num_aggressive] * num_aggressive
                all_available_actions = available_aggressive_actions
            # If no aggressive actions are available, only use preferred actions
            elif num_aggressive == 0:
                probabilities = [1 / num_preferred] * num_preferred
                all_available_actions = available_preferred_actions
            else:
                # Assign probabilities
                preferred_prob_each = preferred_probability / num_preferred
                aggressive_prob_each = aggressive_probability / num_aggressive

                probabilities = (
                    [preferred_prob_each] * num_preferred +
                    [aggressive_prob_each] * num_aggressive
                )

                all_available_actions = available_preferred_actions + available_aggressive_actions

            # Print the probabilities for debugging
            print(f"Available actions: {all_available_actions}")
            print(f"Probabilities: {probabilities}")

            # Choose an action based on the defined probabilities
            chosen_action = random.choices(all_available_actions, probabilities, k=1)[0]

            return chosen_action

        chosen_play = choose_best_play(plays)
        attack_on = ""

        def get_players_except_self(rational_knowledge, self_player_id):
            return [player for player in rational_knowledge["players"].values() if player["id"] != self_player_id]

        self_player_id = rational_knowledge["player"]["id"]
        players_except_self = get_players_except_self(rational_knowledge, self_player_id)

        if chosen_play in plays2:
            

            attack_on = random.choices(players_except_self)[0]["id"]

        return chosen_play, attack_on

    @staticmethod
    @tool("final_answer_play")
    def final_answer_tool_play(play: str, attack_on: str, quote: str):
            """
        Returns a response indicating what action was played and provides {player}'s quote.

        Args:
        play (str): Indicates what action is being taken.
        quote (str): The quote from {player} during the block action.'
        attack_on (str):  this is the person on which the play is being attacked.
        """
            
            return ""

    @staticmethod
    def run_query_agent_play(state: list):
        query_agent_runnable = create_openai_tools_agent(
            llm=ChatOpenAI(temperature=0,model_name="gpt-4o"),
            tools=[PlayFanAgent.play_tool],
            prompt=PlayFanAgent.play_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_play_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = PlayFanAgent.play_tool.invoke(json.loads(tool_call["function"]["arguments"]))
        return {"intermediate_steps": [{"play": str(out)}]}

    @staticmethod
    def play_final_answer(state: list):
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

        Your current action is making a play.
        The play should be one from the following, use exact words:

        plays = [
            "Income",
            "Foreign Aid",
            "Coup",
            "Tax",
            "Assassinate",
            "Steal",
            "Swap"
        ]

        if the play is one of Steal, Assassinate, or Coup, attack_on is attack_on from the previous round; otherwise, it's ""
        CONTEXT: {context}

        What do you play given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
        """


        final_answer_llm = ChatOpenAI(temperature=0,model_name="gpt-4o").bind_tools([PlayFanAgent.final_answer_tool_play], tool_choice="final_answer_play")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}

    