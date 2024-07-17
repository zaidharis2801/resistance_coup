from typing import List
from src.models.state.player_state import PlayerState

class GameState:
    def __init__(self):
        self.player_states: List[PlayerState] = []

    def add_player_state(self, player_state: PlayerState):
        self.player_states.append(player_state)

    def __str__(self):
        return '\n'.join([str(player_state) for player_state in self.player_states])