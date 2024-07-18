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


from src.agents.ActionAgents.peter_helper_file import CoupGame
# Load environment variables from .env file
load_dotenv('.env')

class PlayAgentState(TypedDict):
    rational_knowledge: str
    avalaible_actions : list[str]
    agent_out: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

class PlayLogicAgent:
    play_prompt = PromptTemplate.from_template( f"""
        You are playing the game of Coup as "Uncle Peter". Your personality is logical and meticulous, analyzing every possible outcome before deciding on the best course of action. You value precision and careful planning in all your decisions.

        You have a thorough understanding of game theory and statistical analysis. You frequently study game mechanics and probabilities, ensuring that your moves are always well-calculated.

        You avoid bluffing and high-risk actions like assassination unless they are statistically advantageous. You prefer actions that provide a consistent and long-term benefit.

        When making a move, you always articulate something that reflects your logical and meticulous nature. Your responses should always include:
        1) What Uncle Peter said while making that move.
        2) What move did Uncle Peter make.

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
        self.graph.add_node("query_agent_play", PlayLogicAgent.run_query_agent_play)
        self.graph.add_node("play", PlayLogicAgent.execute_play_tool)
        self.graph.add_node("play_final_answer", PlayLogicAgent.play_final_answer)

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
        str: The play Sam is making.
        """
        rational_knowledge = json.loads(rational_knowledge)


        all_players = rational_knowledge["players"]
        
        own_cards = rational_knowledge["own_cards"]
        gold_coins = rational_knowledge["player"]["coins"]

        plays2 = ["Coup", "Assassinate", "Steal"]


        Pc_Duke = rational_knowledge["card_counts"]["Duke"] / rational_knowledge["unknown_cards"]
        Pc_Contessa = rational_knowledge["card_counts"]["Contessa"] / rational_knowledge["unknown_cards"]
        Pc_Captain = rational_knowledge["card_counts"]["Captain"] / rational_knowledge["unknown_cards"]
        Pc_Ambassador = rational_knowledge["card_counts"]["Ambassador"] / rational_knowledge["unknown_cards"]

        game = CoupGame(len(rational_knowledge["players"]), len(rational_knowledge["players"]) - 1, Pc_Duke, Pc_Contessa, Pc_Captain, Pc_Ambassador, gold_coins, own_cards)
        chosen_play, best_points = game.get_best_action()
        def get_players_except_self(rational_knowledge, self_player_id):
                return [player for player in rational_knowledge["players"].values() if player["id"] != self_player_id]

        self_player_id = rational_knowledge["player"]["id"]
        players_except_self = get_players_except_self(rational_knowledge, self_player_id)
        attack_on = ""
        if chosen_play in plays2 and players_except_self:
                attack_on = random.choice(players_except_self)["id"]
        
        
        return chosen_play,attack_on

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
            tools=[PlayLogicAgent.play_tool],
            prompt=PlayLogicAgent.play_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_play_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = PlayLogicAgent.play_tool.invoke(json.loads(tool_call["function"]["arguments"]))
        return {"intermediate_steps": [{"play": str(out)}]}

    @staticmethod
    def play_final_answer(state: list):
        context = state["intermediate_steps"][-1]
        prompt = f"""
        You are playing the game of Coup as "Uncle Peter". Your personality is logical and meticulous, analyzing every possible outcome before deciding on the best course of action. You value precision and careful planning in all your decisions.

        You have a thorough understanding of game theory and statistical analysis. You frequently study game mechanics and probabilities, ensuring that your moves are always well-calculated.

        You avoid bluffing and high-risk actions like assassination unless they are statistically advantageous. You prefer actions that provide a consistent and long-term benefit.

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


        final_answer_llm = ChatOpenAI(temperature=0,model_name="gpt-4o").bind_tools([PlayLogicAgent.final_answer_tool_play], tool_choice="final_answer_play")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}

    