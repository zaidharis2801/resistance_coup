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

class PlayRandomAgent:
    play_prompt = PromptTemplate.from_template(f"""
        You are playing the game of Coup as "Cousin Sam". Your personality is unpredictable and whimsical, and you enjoy the element of surprise and the chaos it brings. You find fun in the randomness of your actions, keeping everyone on their toes.

        You have a basic understanding of the game rules but do not adhere to any specific strategy. You embrace the randomness of your decisions, making you an unpredictable player.

        Your behavior includes:
        - Actions: You choose actions completely at random without any specific strategy. This includes randomly selecting when to challenge or block other players' actions.
        - Pattern: You do not follow any pattern or logic in decision-making.
        - Flexibility: You can take any action available at any time without prioritizing one over another.

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

        Now, simulate making a play with the following details:
            Player Knowledge: {{rational_knowledge}}

        What do you play given the current context? Just say why in colloquial terms as if you are saying to your fellow players.

        {{agent_scratchpad}}
        """)

    def __init__(self) -> None:


        self.llm = ChatOpenAI(temperature=0, openai_api_key=os.getenv('OPENAI_API_KEY'))
        self.player = "Sam"

        self.graph = StateGraph(PlayAgentState)
        self.graph.add_node("query_agent_play", PlayRandomAgent.run_query_agent_play)
        self.graph.add_node("play", PlayRandomAgent.execute_play_tool)
        self.graph.add_node("play_final_answer", PlayRandomAgent.play_final_answer)

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

        plays = available_actions
        plays2 = ["Coup", "Assassinate", "Steal"]

        # Sam's choices are completely random
        chosen_play = random.choice(plays)
        attack_on = ""

        def get_players_except_self(rational_knowledge, self_player_id):
            return [player for player in rational_knowledge["players"].values() if player["id"] != self_player_id]

        self_player_id = rational_knowledge["player"]["id"]
        players_except_self = get_players_except_self(rational_knowledge, self_player_id)

        if chosen_play in plays2 and players_except_self:
            attack_on = random.choice(players_except_self)["name"]

        return chosen_play, attack_on
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

        plays = available_actions
        plays2 = ["Coup", "Assassinate", "Steal"]

        # Sam's choices are completely random
        chosen_play = random.choice(plays)
        attack_on = ""

        def get_players_except_self(rational_knowledge, self_player_id):
            return [player for player in rational_knowledge["players"].values() if player["id"] != self_player_id]

        self_player_id = rational_knowledge["player"]["id"]
        players_except_self = get_players_except_self(rational_knowledge, self_player_id)

        if chosen_play in plays2 and players_except_self:
            attack_on = random.choice(players_except_self)["id"]

        return chosen_play, attack_on

    @staticmethod
    def play_tool2(rational_knowledge: str, available_actions: list):
        """
        Simulates making a play in the game Coup.

        Args:
        rational_knowledge (str): The knowledge base of the rational player in JSON string form.
        available_actions (list): The list of available actions for the player.

        Returns:
        str: The play Sam is making.
        """
        rational_knowledge = json.loads(rational_knowledge)

        plays = available_actions
        plays2 = ["Coup", "Assassinate", "Steal"]

        # Sam's choices are completely random
        chosen_play = random.choice(plays)
        attack_on = ""

        def get_players_except_self(rational_knowledge, self_player_id):
            return [player for player in rational_knowledge["players"].values() if player["id"] != self_player_id]

        self_player_id = rational_knowledge["player"]["id"]
        players_except_self = get_players_except_self(rational_knowledge, self_player_id)

        if chosen_play in plays2 and players_except_self:
            attack_on = random.choice(players_except_self)["id"]

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
            tools=[PlayRandomAgent.play_tool],
            prompt=PlayRandomAgent.play_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_play_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = PlayRandomAgent.play_tool2(state["rational_knowledge"],state["available"])
        return {"intermediate_steps": [{"play": str(out)}]}


    @staticmethod
    def play_final_answer(state: list):
        context = state["intermediate_steps"][-1]
        prompt = f"""
        You are playing the game of Coup as "Cousin Sam". Your personality is unpredictable and whimsical, and you enjoy the element of surprise and the chaos it brings. You find fun in the randomness of your actions, keeping everyone on their toes.

        You have a basic understanding of the game rules but do not adhere to any specific strategy. You embrace the randomness of your decisions, making you an unpredictable player.

        Your behavior includes:
        - Actions: You choose actions completely at random without any specific strategy. This includes randomly selecting when to challenge or block other players' actions.
        - Pattern: You do not follow any pattern or logic in decision-making.
        - Flexibility: You can take any action available at any time without prioritizing one over another.

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

        if the play is one of Steal, Assassinate, or Coup, attack_on is chosen randomly; otherwise, it's ""
        CONTEXT: {context}

        What do you play given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
        """


        final_answer_llm = ChatOpenAI(temperature=0,model_name="gpt-4o").bind_tools([PlayRandomAgent.final_answer_tool_play], tool_choice="final_answer_play")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}

