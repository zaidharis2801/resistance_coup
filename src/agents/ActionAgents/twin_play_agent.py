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

class PlayTwinAgent:
    play_prompt = PromptTemplate.from_template(f"""
    You are playing the game of Coup as "The Twin Strategists". Your personality is a blend of two distinct approaches: aggressive and cautious, embodied by the twins Tom and Jerry.

    - Tom: Aggressive and bold, Tom thrives on taking high-risk strategies that aim to weaken opponents quickly. He is always looking for opportunities to make daring moves and put pressure on other players.
    - Jerry: Cautious and strategic, Jerry prefers defensive and conservative strategies that ensure long-term survival. He focuses on building a strong position and protecting their combined assets.

    You have a comprehensive understanding of game dynamics, with Tom specializing in aggressive tactics and Jerry in defensive strategies. Your decisions are influenced by both perspectives to create a balanced approach to the game.

    When making a move, the input will be sent to both Tom and Jerry who will then make a decision which will be sent to the arbitrator for final judgment. Your responses should always include:
    1) What Tom and Jerry decided while making that move.
    2) What move did The Twin Strategists make based on their combined input.

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

    The input from the game will be sent to both Tom and Jerry who will then make a decision which will be sent to the arbitrator for final judgment.
""")

    def __init__(self) -> None:


        self.llm = ChatOpenAI(temperature=0, openai_api_key=os.getenv('OPENAI_API_KEY'))
        self.player = "Dad"

        self.graph = StateGraph(PlayAgentState)
        self.graph.add_node("SynergyMediator", PlayTwinAgent.run_query_agent_play)
        self.graph.add_node("BoldActionNode_Tom", PlayTwinAgent.execute_play_tool)
        self.graph.add_node("CautiousActionNode_Jerry", PlayTwinAgent.execute_play_tool2)
        self.graph.add_node("Agent_DecisionEngine_(arbitrator)", PlayTwinAgent.play_final_answer)

        self.graph.set_entry_point("SynergyMediator")
        self.graph.add_edge("SynergyMediator", "BoldActionNode_Tom")
        self.graph.add_edge("SynergyMediator", "CautiousActionNode_Jerry")
        self.graph.add_edge("CautiousActionNode_Jerry", "Agent_DecisionEngine_(arbitrator)")
        self.graph.add_edge("BoldActionNode_Tom", "Agent_DecisionEngine_(arbitrator)")
        self.graph.add_edge("Agent_DecisionEngine_(arbitrator)", END)

        self.runnable = self.graph.compile()

    def get_result(self, inputs_play):
        out = self.runnable.invoke(inputs_play)
        return out
      
     

    @staticmethod 
    def play_tool(rational_knowledge: str,available:list):      
        rational_knowledge = json.loads(rational_knowledge)


        plays =available
        plays2 = [
            "Coup",
            "Assassinate",
            "Steal"
        ]
        def choose_best_play(available_actions):
           # Preferred actions with higher probability
            preferred_actions = ["Coup", "Assassinate", "Steal"]
            # Other actions
            other_actions = ["Income", "Foreign Aid", "Tax", "Swap"]

            # Filter the available preferred and other actions
            available_preferred_actions = [action for action in preferred_actions if action in available_actions]
            available_other_actions = [action for action in other_actions if action in available_actions]

            # Define probabilities
            preferred_probability = 0.7
            other_probability = 0.3

            # Calculate number of available preferred and other actions
            num_preferred = len(available_preferred_actions)
            num_other = len(available_other_actions)

            # If no preferred actions are available, only use other actions
            if num_preferred == 0:
                probabilities = [1 / num_other] * num_other
                all_available_actions = available_other_actions
            # If no other actions are available, only use preferred actions
            elif num_other == 0:
                probabilities = [1 / num_preferred] * num_preferred
                all_available_actions = available_preferred_actions
            else:
                # Assign probabilities
                preferred_prob_each = preferred_probability / num_preferred
                other_prob_each = other_probability / num_other

                probabilities = (
                    [preferred_prob_each] * num_preferred +
                    [other_prob_each] * num_other
                )

                all_available_actions = available_preferred_actions + available_other_actions

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
           

            attack_on = random.choices(players_except_self)[0]['name']

        return chosen_play, attack_on
        
    @staticmethod 
    def play_tool2(rational_knowledge: str,available:list):
    
        rational_knowledge = json.loads(rational_knowledge)

        plays = available
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
           

            attack_on = random.choices(players_except_self)[0]["name"]

        return chosen_play, attack_on
    @staticmethod
    @tool("final_answer_play")
    def final_answer_tool_play(play: str, attack_on: str, quote: str):
         """
    Returns a response indicating what action was played and provides the arbitrators's quote.

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
            tools=[PlayTwinAgent.play_tool],
            prompt=PlayTwinAgent.play_prompt
        )
        agent_out = query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}

    @staticmethod
    def execute_play_tool(state: list):
        action = state["agent_out"]
        out = PlayTwinAgent.play_tool(state["rational_knowledge"],state["available"])
        return {"intermediate_steps": [{"play": str(out)}]}
    @staticmethod
    def execute_play_tool2(state: list):
        action = state["agent_out"]
        out = PlayTwinAgent.play_tool2(state["rational_knowledge"],state["available"])
        return {"intermediate_steps": [{"play": str(out)}]}

    @staticmethod
    def play_final_answer(state: list):
        context_tom = state["intermediate_steps"][-1]
        context_jerry = state["intermediate_steps"][-2]
        print(context_tom)
        print(context_jerry)
        prompt = f"""
    You are playing the game of Coup as "The Arbitrator". Your role is to balance the aggressive and cautious strategies of the Twin Strategists, Tom and Jerry, to make the most effective decision.

    - Tom: Aggressive and bold, Tom thrives on taking high-risk strategies that aim to weaken opponents quickly. He is always looking for opportunities to make daring moves and put pressure on other players.
    - Jerry: Cautious and strategic, Jerry prefers defensive and conservative strategies that ensure long-term survival. He focuses on building a strong position and protecting their combined assets.

    You have a comprehensive understanding of game dynamics, combining Tom's expertise in aggressive tactics and Jerry's knowledge of defensive strategies to form a balanced and effective approach.

    Your current action is making a play based on the inputs from both Tom and Jerry.
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

    If the play is one of Steal, Assassinate, or Coup, attack_on is attack_on from the previous round; otherwise, it's ""
    CONTEXT from Tom: {context_tom}
    CONTEXT from Jerry: {context_jerry}

    What do you play given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
"""
        final_answer_llm = ChatOpenAI(temperature=0,model_name="gpt-4o").bind_tools([PlayTwinAgent.final_answer_tool_play], tool_choice="final_answer_play")
        out = final_answer_llm.invoke(prompt)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}

