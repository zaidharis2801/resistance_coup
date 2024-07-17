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
import random
from langchain_core.agents import AgentFinish
import json


class AgentState(TypedDict):
        action: str
        character: str
        target: str
        cards: list
        probability: int
        agent_out: Union[AgentAction, AgentFinish, None]
        intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]

class BlockAgentMom:
    
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

        self.llm  = ChatOpenAI(temperature=0,model_name="gpt-4o")
        self.player = "Dad"

        self.blockPrompt = PromptTemplate.from_template(
            """
    You are playing the game of Coup as "Dad". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

    You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.

    You avoid straightforward and predictable actions like income, as they do not support your strategy of deception and bluffing.

    When making a move, you always articulate something that reflects your charismatic and persuasive nature. Your responses should always include:
    1) What Dad said while making that move.
    2) What move did Dad make.

    Now, simulate the blocking action with the following details:
    Action: {action}
    Character: {character}
    Target: {target}
    Cards: {cards}
    Bluff Probability: {probability}%

    {agent_scratchpad}
"""
        )
    
     

            

        self.graph = StateGraph(AgentState)

# we have four nodes that will consume our agent state and modify
# our agent state based on some internal process
        self.graph.add_node("query_agent", BlockAgentMom.run_query_agent)
        self.graph.add_node("block", BlockAgentMom.execute_block)

        self.graph.add_node("block_final_answer", BlockAgentMom.block_final_answer)

        # our self.graph will always begin with the query agent
        self.graph.set_entry_point("query_agent")

        self.graph.add_edge("query_agent", "block")
        self.graph.add_edge("block", "block_final_answer")
        self.graph.add_edge("block_final_answer", END)

        self.runnable = self.graph.compile()

        
    def get_result(self,inputs_block):
        out = self.runnable.invoke(inputs_block)
        return out
    @staticmethod
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
    

    @staticmethod
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
    
    @staticmethod
    def run_query_agent(state: list):
        print("> run_query_agent")
        blockPrompt = PromptTemplate.from_template(
            """
    You are playing the game of Coup as "Dad". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

    You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.

    You avoid straightforward and predictable actions like income, as they do not support your strategy of deception and bluffing.

    When making a move, you always articulate something that reflects your charismatic and persuasive nature. Your responses should always include:
    1) What Dad said while making that move.
    2) What move did Dad make.

    Now, simulate the blocking action with the following details:
    Action: {action}
    Character: {character}
    Target: {target}
    Cards: {cards}
    Bluff Probability: {probability}%

    {agent_scratchpad}
"""
        )
        

        query_agent_runnable=create_openai_tools_agent(
            llm=ChatOpenAI(temperature=0,model_name="gpt-4o"),
            tools=[BlockAgentMom.block_tool_player],
            prompt=blockPrompt
)   
        agent_out =query_agent_runnable.invoke(state)
        return {"agent_out": agent_out}
    @staticmethod
    def execute_block(state: list):
        print("> execute_block")
        action = state["agent_out"]
        tool_call = action[-1].message_log[-1].additional_kwargs["tool_calls"][-1]
        out = BlockAgentMom.block_tool_player.invoke(
            json.loads(tool_call["function"]["arguments"])
        )
        return {"intermediate_steps": [{"block": str(out)}]}
    
    @staticmethod
    def block_final_answer(state: list):
        print("> final_answer")

        context = state["intermediate_steps"][-1]

        prompt2 = f"""You are You are playing the game of Coup as "Dad". Your personality is charismatic and charming, and you enjoy the art of persuasion. Your bluffs are incredibly convincing, making it difficult for others to discern your true intentions. You thrive on the challenge of outwitting your opponents through deception and psychological tactics.

    You have an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making you a master of misinformation. Your preferred cards are Duke and Assassin, and your favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.
    Your current action is blocking.

    CONTEXT: {context}

    Do you block given the current context. Just say why in colloquial terms as if you are saying to your fellow players.
    """
        final_answer_llm = ChatOpenAI(temperature=0,model_name="gpt-4o").bind_tools([BlockAgentMom.final_answer_tool_blocking], tool_choice="final_answer")

        out = final_answer_llm.invoke(prompt2)
        function_call = out.additional_kwargs["tool_calls"][-1]["function"]["arguments"]
        return {"agent_out": function_call}




