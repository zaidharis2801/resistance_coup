import os
from langchain.agents import create_openai_tools_agent
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_core.agents import AgentFinish, AgentAction
import json
from typing import TypedDict, Annotated, List, Union
import operator
from langgraph.graph import StateGraph, END
import random
from src.models.mymodels.playerbase import PlayerBase 
from src.models.mymodels.rationalplayerknowledge import RationalPlayerKnowledge


from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv('.env')

# Access the environment variables
langchain_tracing = os.getenv('LANGCHAIN_TRACING_V2')
langchain_api_key = os.getenv('LANGCHAIN_API_KEY')
openai_api_key2 = os.getenv('OPENAI_API_KEY')
mom = PlayerBase(
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


dad = PlayerBase(
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




own_cards = ['Duke', 'Assassin']
rational_knowledge = RationalPlayerKnowledge(player=dad, total_players=3, players=[mom], own_cards=own_cards)
# Convert to dictionary
rational_knowledge_dict = rational_knowledge.to_dict()
claimant_dict = mom.to_dict()


rational_knowledge_dict_str = json.dumps(rational_knowledge_dict)
claimant_dict_str  = json.dumps(claimant_dict)

class AgentState(TypedDict):
    action: str
    character: str
    target: str
    cards: list
    probability: int
    agent_out: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]
llm = ChatOpenAI(temperature=0,openai_api_key=openai_api_key2)
player = "Dad"
promptstart=f"""
 You are playing the game of Coup as "{player}". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

    You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.

    You avoid straightforward and predictable actions like income, as they do not support your strategy of deception and bluffing.
     When making a move, you always articulate something that reflects your charismatic and persuasive nature. Your responses should always include:

    1) What {player} said while making that move.
    2) What move did {player} make.

"""
promptbase ="""
You are playing the game of Coup as "{player}". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

    You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.
    Your current action is blocking.
"""
prompt1 = PromptTemplate.from_template(
  promptstart+  """


    Now, simulate the blocking action with the following details:
    Action: {action}
    Character: {character}
    Target: {target}
    Cards: {cards}
    Bluff Probability: {probability}%

    {agent_scratchpad}
""")

@tool("block")
def block_tool_player(action: str, character: str, target: str, cards: list, probability: int):
    """
    Block action can only be performed if the person on whom the action is performed.
    Simulates blocking an action in the game Coup with a given probability to bluff.

    Args:
    action (str): The action being blocked.
    character (str): The player performing the block.
    target (str): The player on whom the action is being performed.
    cards (list): The cards held by the player performing the block.
    probability (int): The probability to bluff to block.

    Returns:
    bool: Is the action being blocked by {player}.
    """
    import random

    # Define the blockable actions and the characters that can block them
    blockable_actions = {
        "Foreign Aid": ["Duke"],
        "Assassinate": ["Contessa"],
        "Steal": ["Captain", "Ambassador"]
    }

    if len(cards) == 1 and action == "Assassinate":
        return True

    # Determine if the block is a bluff based on the probability
    required_cards = blockable_actions[action]
    for card in required_cards:
        if card in cards:
            return True

    if random.randint(1, 100) <= probability:
        bluffing = True
    else:
        bluffing = False

    return bluffing

@tool("final_answer")
def final_answer_tool_blocking(
    blocking: bool,
    quote: str
):
    """
    Returns a response indicating whether the action was blocked and provides {player}'s quote.

    Args:
    blocking (bool): Indicates if the action is being blocked.
    quote (str): The quote from {player} during the block action.

    """
    return ""

inputs_block = {
    "action": "Foreign Aid",
    "character": "Duke",
    "target": player,
    "cards": ["Duke", "Assassin"],
    "probability": 100,
    "intermediate_steps": []
}

query_agent_runnable = create_openai_tools_agent(
    llm=llm,
    tools=[block_tool_player],
    prompt=prompt1
)

# Invoke the agent with the inputs
# agent_out_block = query_agent_runnable.invoke(inputs_block)
# print(agent_out_block)

# agent_out_block[-1].message_log[-1].additional_kwargs["tool_calls"][-1]



def run_query_agent(state: list):
    print("> run_query_agent")
    agent_out = query_agent_runnable.invoke(state)
    return {"agent_out": agent_out}

def execute_block(state: list):
    print("> execute_block")
    action = state["agent_out"]
    tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
    out = block_tool_player.invoke(
        json.loads(tool_call["function"]["arguments"])
    )
    return {"intermediate_steps": [{"block": str(out)}]}

final_answer_llm = llm.bind_tools([final_answer_tool_blocking], tool_choice="final_answer")

def block_final_answer(state: list):
    print("> final_answer")

    context = state["intermediate_steps"][-1]

    prompt2 = promptbase+f"""

    CONTEXT: {context}

    Do you block given the current context. Just say why in colloquial terms as if you are saying to your fellow players.
    """
    out = final_answer_llm.invoke(prompt2)
    function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
    return {"agent_out": function_call}

graph = StateGraph(AgentState)

# we have four nodes that will consume our agent state and modify
# our agent state based on some internal process
graph.add_node("query_agent", run_query_agent)
graph.add_node("block", execute_block)

graph.add_node("block_final_answer", block_final_answer)

# our graph will always begin with the query agent
graph.set_entry_point("query_agent")

graph.add_edge("query_agent", "block")
graph.add_edge("block", "block_final_answer")
graph.add_edge("block_final_answer", END)

runnable = graph.compile()

inputs_block = {
    "action": "Assassinate",
    "character": player,
    "target": player,
    "cards": ["Duke", "Duke"],
    "probability": 0,
    "intermediate_steps": []
}

out = runnable.invoke(inputs_block)
print(out["agent_out"])
