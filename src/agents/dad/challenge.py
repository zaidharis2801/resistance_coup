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

class ChallengeAgentState(TypedDict):
    claim: str
    claimant: str
    rational_knowledge: str
    agent_out: Union[AgentAction, AgentFinish, None]
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

llm = ChatOpenAI(temperature=0)
player = "Dad"
promptbase1=f"""
You are playing the game of Coup as "{player}". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.

You avoid straightforward and predictable actions like income, as they do not support your strategy of deception and bluffing.

When making a move, you always articulate something that reflects your charismatic and persuasive nature. Your responses should always include:
1) What {player} said while making that move.
2) What move did {player} make.


"""
promptbase2 =f"""
 You are playing the game of Coup as {player}. Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

    You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.

"""
challenge_prompt = PromptTemplate.from_template(promptbase1+f"""
Now, simulate the challenge action with the following details:
Player Knowledge: {{rational_knowledge}}
Claimant: {{claimant}}
Claim: {{claim}}

{{agent_scratchpad}}
""")

@tool("challenge")
def challenge_tool(rational_knowledge: str, claimant: str, claim: str):
    """
    Simulates challenging a claim in the game Coup.

    Args:
    rational_knowledge (dict): The knowledge base of the rational player in dictionary form.
    claimant (dict): The player making the claim in dictionary form.
    claim (str): The claim being challenged.

    Returns:
    bool: is {player} challenging the action.
    """
    claimant = json.loads(claimant)
    rational_knowledge = json.loads(rational_knowledge)

    def calculate_probability_of_truth(pc, Pt_x):
        """
        Calculate the probability that person x is telling the truth when they claim they have card c.
        """
        P_B = pc + (1 - Pt_x) * (1 - pc)
        P_A_given_B = pc / P_B
        return P_A_given_B

    card_counts = rational_knowledge.get("card_counts", {})
    unknown_cards = rational_knowledge.get("unknown_cards", 0)
    probability_to_truth = 1 - claimant.get("probability_to_bluff", 0)
    pc = card_counts.get(claim, 0) / unknown_cards
    Pt_x = probability_to_truth
    probability_of_truth = calculate_probability_of_truth(pc, Pt_x)

    return probability_of_truth < 0.7

@tool("final_answer_challenge")
def final_answer_tool_challenge(challenge: bool, quote: str):
    """
    Returns a response indicating whether the action was challenged and provides {player}'s quote.

    Args:
    blocking (bool): Indicates if the action is being blocked.
    quote (str): The quote from {player} during the block action.
    """
    return ""

inputs_challenge = {
    "rational_knowledge": json.dumps(rational_knowledge.to_dict()),
    "claimant": json.dumps(mom.to_dict()),
    "claim": "Duke",
    "intermediate_steps": []
}

query_agent_runnable_challenge = create_openai_tools_agent(
    llm=llm,
    tools=[challenge_tool],
    prompt=challenge_prompt
)

agent_out_challenge = query_agent_runnable_challenge.invoke(inputs_challenge)
print(agent_out_challenge)

def run_query_agent_challenge(state: list):
    print("> run_query_agent_challenge")
    agent_out = query_agent_runnable_challenge.invoke(state)
    return {"agent_out": agent_out}

def execute_challenge_tool(state: list):
    print("> execute_challenge_tool")
    action = state["agent_out"]
    tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
    out = challenge_tool.invoke(json.loads(tool_call["function"]["arguments"]))
    return {"intermediate_steps": [{"challenge": str(out)}]}

final_answer_llm_challenge = llm.bind_tools([final_answer_tool_challenge], tool_choice="final_answer_challenge")

def challenge_final_answer(state: list):
    print("> final_answer")
    context = state["intermediate_steps"][-1]
    prompt = promptbase2+f"""
   Your current action is challenging.

    CONTEXT: {context}

    Do you challenge given the current context? Just say why in colloquial terms as if you are saying to your fellow players.
    """
    out = final_answer_llm_challenge.invoke(prompt)
    function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
    return {"agent_out": function_call}

challenge_graph = StateGraph(ChallengeAgentState)

challenge_graph.add_node("query_agent_challenge", run_query_agent_challenge)
challenge_graph.add_node("challenge", execute_challenge_tool)
challenge_graph.add_node("challenge_final_answer", challenge_final_answer)

challenge_graph.set_entry_point("query_agent_challenge")
challenge_graph.add_edge("query_agent_challenge", "challenge")
challenge_graph.add_edge("challenge", "challenge_final_answer")
challenge_graph.add_edge("challenge_final_answer", END)

challenge_runnable = challenge_graph.compile()

out = challenge_runnable.invoke(inputs_challenge)
print(out["agent_out"])
