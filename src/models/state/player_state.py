# `player_state.py` in the `state` directory

from typing import List, Optional
from src.models.card import Card
from src.models.action import Action

class PlayerState:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.cards: List[Card] = []
        self.coins: int = 2
        self.current_turn: int
        self.current_turn_action: Optional[Action] = None

    def __str__(self):
        return (f"Player ID: {self.player_id}, "
                f"Cards: {', '.join([str(card) for card in self.cards])}, "
                f"Coins: {self.coins}, "
                f"Current Turn: {self.current_turn}, "
                f"Current Action: {self.current_turn_action}")


