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

# Load environment variables from .env file
load_dotenv('.env')

class PlayAgentState(TypedDict):
    rational_knowledge: str
    avalaible_actions : list[str]
    agent_out: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

class PlayDadAgent:
    play_prompt = PromptTemplate.from_template(f"""
        You are playing the game of Coup as "Dad". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

        You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.

        You avoid straightforward and predictable actions like income, as they do not support your strategy of deception and bluffing.

        When making a move, you always articulate something that reflects your charismatic and persuasive nature. Your responses should always include:
        1) What Dad said while making that move.
        2) What move did Dad make.

        These are the plays you can make:
            Play: Starting with the player to the left of the dealer and going clockwise, players take turns performing one of the available actions.
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

        self.llm = ChatOpenAI(temperature=0, openai_api_key=os.getenv('OPENAI_API_KEY'))
        self.player = "Dad"

        self.graph = StateGraph(PlayAgentState)
        self.graph.add_node("query_agent_play", PlayDadAgent.run_query_agent_play)
        self.graph.add_node("play", PlayDadAgent.execute_play_tool)
        self.graph.add_node("play_final_answer", PlayDadAgent.play_final_answer)

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
    def play_tool(rational_knowledge: str,avalaible_actions:list):
        """
    Simulates making a play in the game Coup.

    Args:
    rational_knowledge (dict): The knowledge base of the rational player in dictionary form.


    Returns:
    str: what is the play dad is making
    """
        rational_knowledge = json.loads(rational_knowledge)
        card_counts = rational_knowledge.get("card_counts", {})
        plays = [
            # "Income",
            # "Foreign Aid",
            # "Swap",
            # "Tax",
            "Coup",
            "Assassinate",
            "Steal"
        ]
        plays =avalaible_actions
        plays2 = [
            "Coup",
            "Assassinate",
            "Steal"
        ]

        chosen_play = random.choice(plays)
        attack_on_name = ""
        def get_players_except_self(rational_knowledge, self_player_id):
            return [player for player in rational_knowledge["players"].values() if player["id"] != self_player_id]
        self_player_id = rational_knowledge["player"]["id"]
        players_except_self = get_players_except_self(rational_knowledge, self_player_id)

        if chosen_play in plays2:
            attack_on = random.choice(players_except_self)["id"]
            attack_on_name = rational_knowledge["players"]["Player" + str(attack_on)]["id"]
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
            llm=ChatOpenAI(temperature=0),
            tools=[PlayDadAgent.play_tool],
            prompt=PlayDadAgent.play_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_play_tool(state: list):
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = PlayDadAgent.play_tool.invoke(json.loads(tool_call["function"]["arguments"]))
        return {"intermediate_steps": [{"play": str(out)}]}

    @staticmethod
    def play_final_answer(state: list):
        context = state["intermediate_steps"][-1]
        prompt = f"""
        You are playing the game of Coup as "Dad". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the play of outwitting your opponents through deception and psychological tactics.

        You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.
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
        final_answer_llm = ChatOpenAI(temperature=0).bind_tools([PlayDadAgent.final_answer_tool_play], tool_choice="final_answer_play")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}