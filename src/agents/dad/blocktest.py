from src.agents.dad.block2 import BlockAgentDad
from src.agents.dad.challenge_dad import ChallengeDadAgent
import time
import json
from src.models.mymodels.rationalplayerknowledge import RationalPlayerKnowledge
from src.models.mymodels.playerbase import PlayerBase

# Initialize BlockAgent

start_time = time.time()
blockagent = ChallengeDadAgent()
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Time taken for ChallengeDadAgent: {elapsed_time:.6f} seconds")
# Define inputs

mom = PlayerBase(id="P1", name="Mom", coins=2, prompt_str="Mom is a gullible and innocent player, often easily convinced by others.", details="Mom is known for her trusting nature and tendency to believe in the good of others.", tags=["gullible", "innocent"], numberofcards=2, alive=True, probability_to_bluff=0.1, current_quote="I don't think you should challenge me on this!")

dad = PlayerBase(id="P2", name="Dad", coins=2, prompt_str="Dad is a charismatic and charming player, who enjoys the art of persuasion. His bluffs are incredibly convincing, making it difficult for others to discern his true intentions. He thrives on the challenge of outwitting his opponents through deception and psychological tactics.", details="Dad has an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making him a master of misinformation. His preferred cards are Duke and Assassin, and his favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.", tags=["charismatic", "charming", "persuasive"], numberofcards=2, alive=True, probability_to_bluff=0.9, current_quote="I assure you, I'm the Duke. Anyone who doubts me will regret it.")

own_cards = ['Duke', 'Assassin']
rational_knowledge = RationalPlayerKnowledge(player=dad, total_players=3, players=[mom], own_cards=own_cards)

# Function to log time for get_result
def log_time_for_get_result(agent, inputs):
    start_time = time.time()
    result = agent.get_result(inputs)
    print(result)
    print(result["agent_out"])
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken for get_result: {elapsed_time:.6f} seconds")
    return result

# Usage Example
inputs_challenge = {
    "rational_knowledge": json.dumps(RationalPlayerKnowledge(player=dad, total_players=3, players=[mom], own_cards=['Duke', 'Assassin']).to_dict()),
    "claimant": json.dumps(mom.to_dict()),
    "claim": "Duke",
    "intermediate_steps": []
}


# Call and log time for the first function call
log_time_for_get_result(blockagent, inputs_challenge)

# Call and log time for the second function call
log_time_for_get_result(blockagent, inputs_challenge)