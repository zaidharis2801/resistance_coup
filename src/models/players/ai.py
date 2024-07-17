import random
import time
from typing import List, Optional, Tuple
import json
from src.models.action import Action
from src.models.card import Card
from src.models.players.base import BasePlayer
from src.utils.print import print_text, print_texts
from src.models.action import *

class AIPlayer(BasePlayer):
    is_ai: bool = True

    def choose_action(self, other_players: List[BasePlayer],knowledgebase,play_agent) -> Tuple[Action, Optional[BasePlayer]]:
        """Choose the next action to perform"""

        available_actions = self.available_actions()

        print_text(f"[bold magenta]{self}[/] is thinking...", with_markup=True)
        rational_knowledge_dict_str = json.dumps(knowledgebase.to_dict())
        inputs_play2 = {
            "rational_knowledge": rational_knowledge_dict_str,
            "intermediate_steps": []
        }

        out = play_agent.get_result(inputs_play2)
        output_dict = json.loads(out["agent_out"])
        # time.sleep(1)
        action_map = {
            "Income": IncomeAction(),
            "Foreign Aid": ForeignAidAction(),
            "Coup": CoupAction(),
            "Tax": TaxAction(),
            "Assassinate": AssassinateAction(),
            "Steal": StealAction(),
            "Exchange": ExchangeAction()
        }
        play = output_dict.get("play")
        

        target_action = action_map.get(play, random.choice(available_actions))
        
        
        # Coup is only option
        if len(available_actions) == 1:
            player = random.choice(other_players)
            return available_actions[0], player

        # Pick any other random choice (might be a bluff)
        
        # target_action  = random.choice(available_actions)
        print("#"*80)
        print(output_dict)
        target_player = None

        if target_action.requires_target:
            target_player = random.choice(other_players)

        # Make sure we have a valid action/player combination
        while not self._validate_action(target_action, target_player):
            target_action = random.choice(available_actions)
            if target_action.requires_target:
                target_player = random.choice(other_players)

        return target_action, target_player

    def determine_challenge(self, player: BasePlayer) -> bool:
        """Choose whether to challenge the current player"""

        # 20% chance of challenging
        return random.randint(0, 4) == 0

    def determine_counter(self, player: BasePlayer) -> bool:
        """Choose whether to counter the current player's action"""

        # 10% chance of countering
        return random.randint(0, 9) == 0

    def remove_card(self) -> None:
        """Choose a card and remove it from your hand"""

        # Remove a random card
        discarded_card = self.cards.pop(random.randrange(len(self.cards)))
        print_texts(f"{self} discards their ", (f"{discarded_card}", discarded_card.style), " card")

    def choose_exchange_cards(self, exchange_cards: list[Card]) -> Tuple[Card, Card]:
        """Perform the exchange action. Pick which 2 cards to send back to the deck"""

        self.cards += exchange_cards
        random.shuffle(self.cards)
        print_text(f"{self} exchanges 2 cards")

        return self.cards.pop(), self.cards.pop()
