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

# Load environment variables from .env file
load_dotenv('.env')

class PlayAgentState(TypedDict):
    rational_knowledge: str
    available : list[str]
    agent_out: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

class PlayMomAgent:
    play_prompt = PromptTemplate.from_template(f"""
        You are playing the game of Coup as "Mom". Your personality is caring and protective, focusing on keeping everyone safe and happy. You prefer to play it safe, avoid unnecessary conflicts, and ensure your survival in the game.

You have a good understanding of game mechanics and strategies, often discussing gameplay with friends and family. You prioritize actions that ensure your long-term survival over aggressive tactics. Your preferred cards are Contessa and Duke, and your favorite actions are taking income, foreign aid, and blocking assassination attempts.

You avoid challenging other players’ claims and aggressive actions like assassination and coup, focusing instead on defensive and safe moves, except when playing against Dad, against whom you are very aggressive.

When making a move, you always articulate something that reflects your caring and protective nature. Your responses should always include:
1) What Mom said while making that move.
2) What move did Mom make.

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
    """)

    def __init__(self) -> None:


        self.llm = ChatOpenAI(temperature=0, openai_api_key=os.getenv('OPENAI_API_KEY'))
        self.player = "Mom"

        self.graph = StateGraph(PlayAgentState)
        self.graph.add_node("query_agent_play", PlayMomAgent.run_query_agent_play)
        self.graph.add_node("play", PlayMomAgent.execute_play_tool)
        self.graph.add_node("play_final_answer", PlayMomAgent.play_final_answer)

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
    def play_tool(rational_knowledge: str,available_actions:list):
        """
    Simulates making a play in the game Coup.

    Args:
    rational_knowledge (dict): The knowledge base of the rational player in dictionary form.


    Returns:
    str: what is the play mom is making
    """
        rational_knowledge = json.loads(rational_knowledge)

        plays = available_actions
        plays2 = ["Coup", "Assassinate", "Steal"]

        def choose_best_play(available_actions):
            preferred_actions = ["Income", "Foreign Aid"]
            aggressive_actions = ["Coup", "Assassinate", "Steal"]

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

            # # Print the probabilities for debugging
            # print(f"Available actions: {all_available_actions}")
            # print(f"Probabilities: {probabilities}")

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
            if len(players_except_self) > 1:
                probabilities = [0.9 if player["id"] == "Player1" else 0.1 / (len(players_except_self) - 1) for player in players_except_self]
            else:
                probabilities = [1.0]  # If there is only one player, attack that player


            # print(f"Attack probabilities: {probabilities}")

            attack_on = random.choices(players_except_self, probabilities, k=1)[0]["name"]

        return chosen_play, attack_on

    @staticmethod  
    def play_tool2(rational_knowledge: str,available_actions:list):
        """
    Simulates making a play in the game Coup.

    Args:
    rational_knowledge (dict): The knowledge base of the rational player in dictionary form.


    Returns:
    str: what is the play mom is making
    """
        rational_knowledge = json.loads(rational_knowledge)

        plays = available_actions
        plays2 = ["Coup", "Assassinate", "Steal"]

        def choose_best_play(available_actions):
            preferred_actions = ["Income", "Foreign Aid"]
            aggressive_actions = ["Coup", "Assassinate", "Steal"]

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
            # print(f"Available actions: {all_available_actions}")
            # print(f"Probabilities: {probabilities}")

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
            if len(players_except_self) > 1:
                probabilities = [0.9 if player["id"] == "Player1" else 0.1 / (len(players_except_self) - 1) for player in players_except_self]
            else:
                probabilities = [1.0]  # If there is only one player, attack that player


            # print(f"Attack probabilities: {probabilities}")

            attack_on = random.choices(players_except_self, probabilities, k=1)[0]["name"]

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
            tools=[PlayMomAgent.play_tool],
            prompt=PlayMomAgent.play_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_play_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = PlayMomAgent.play_tool2(state["rational_knowledge"],state["available"])
        return {"intermediate_steps": [{"play": str(out)}]}


    @staticmethod
    def play_final_answer(state: list):
        context = state["intermediate_steps"][-1]
        prompt = f"""
        You are playing the game of Coup as "Mom". Your personality is caring and protective, focusing on keeping everyone safe and happy. You prefer to play it safe, avoid unnecessary conflicts, and ensure your survival in the game. However, you are very aggressive against Dad.

        You have a good understanding of game mechanics and strategies, often discussing gameplay with friends and family. You prioritize actions that ensure your long-term survival over aggressive tactics. Your preferred cards are Contessa and Duke, and your favorite actions are taking income, foreign aid, and blocking assassination attempts. You avoid challenging other players’ claims and aggressive actions like assassination and coup, focusing instead on defensive and safe moves, except against Dad.

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

        final_answer_llm = ChatOpenAI(temperature=0,model_name="gpt-4o").bind_tools([PlayMomAgent.final_answer_tool_play], tool_choice="final_answer_play")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}

