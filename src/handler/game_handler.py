import random
from enum import Enum
from typing import List, Optional, Tuple, Union
import time
import json
import names
from tqdm import tqdm
from dotenv import load_dotenv
import os
import copy

from src.models.state.game_state import PlayerState 
from src.models.action import Action, ActionType, CounterAction, get_counter_action
from src.models.card import Card, build_deck
from src.models.players.ai import AIPlayer
from src.models.players.base import BasePlayer
from src.models.players.human import HumanPlayer
from src.models.mymodels.playerbase import PlayerBase
from src.models.mymodels.rationalplayerknowledge import RationalPlayerKnowledge

from src.agents.factory.playFactory import PlayAgentFactory
from src.agents.factory.challengeFactory import ChallengeAgentFactory
from src.agents.factory.blockFactory import BlockAgentFactory

# Load environment variables from .env file
from src.utils.game_state import generate_players_table, generate_state_panel
from src.utils.print import (
    build_action_report_string,
    build_counter_report_string,
    print_confirm,
    print_panel,
    print_table,
    print_text,
    print_texts,
)


class ChallengeResult(Enum):
    no_challenge = 0
    challenge_failed = 1
    challenge_succeeded = 2


class ResistanceCoupGameHandler:
    _players: List[BasePlayer] = []
    _current_player_index = 0
    _deck: List[Card] = []
    _number_of_players: int = 0
    _treasury: int = 0
    _playerbases =[]
    _knowledges =[]
    _player_states =[]
    


    def __init__(self, player_name: str, number_of_players: int):
        
        self._number_of_players = number_of_players
       
        # Set up players
        

        mom = PlayerBase(
                                id="Player0",
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
    id="Player1",
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

        self._players.append(AIPlayer(name="Mom"))
        self._players.append(AIPlayer(name="Dad"))

        self._playerbases.append(mom)
        self._playerbases.append(dad)

        self._deck = build_deck()
        self._shuffle_deck()

        self._treasury = 50 - 2 * len(self._players)
        
        num_agents = 5
        self._play_agents = []
        self._block_agents = []
        self._challenge_agents =[]

        self._player_names=["Mom","Dad"]
        
        for i in tqdm(range(len(self._player_names)), desc="Creating AI LangGraph Agents"):
                 
                 
            self._play_agents.append(PlayAgentFactory.create_agent(self._player_names[i]))
            self._challenge_agents.append(ChallengeAgentFactory.create_agent(self._player_names[i]))
            self._block_agents.append(BlockAgentFactory.create_agent(self._player_names[i]))
            print(f"   Created AI agents for : {self._player_names[i]}")
        

       
        for i in range(len(self._players)):
            card1=self._deck.pop()
            card2=self._deck.pop()
            self._players[i].cards.append(card1)
            self._players[i].cards.append(card2)
            self._players[i].coins = 2

            # Includes the player in the game
            self._players[i].is_active = True
            
            self._knowledges.append(RationalPlayerKnowledge(
                player=self._playerbases[i],
                total_players=len(self._players) - 1,
                players=[self._playerbases[j] for j in range(len(self._playerbases)) ],
                
                own_cards =[card1.card_type.value,card2.card_type.value]
    ))
       
       

        

        

    @property
    def current_player(self) -> BasePlayer:
        return self._players[self._current_player_index]

    @property
    def remaining_player(self) -> BasePlayer:
        """Return the only remaining player"""
        return [player for player in self._players if player.is_active][0]

    def print_game_state(self) -> None:
        print_table(generate_players_table(self._players, self._current_player_index))
        print_panel(generate_state_panel(self._deck, self._treasury, self.current_player))

    def _players_without_player(self, excluded_player: BasePlayer):
        players_copy = self._players.copy()
        return [
            player
            for player in players_copy
            if player.is_active and player.name != excluded_player.name
        ]

    def _shuffle_deck(self) -> None:
        random.shuffle(self._deck)

    def setup_game(self) -> None:
        

        # Random starting player
        self._current_player_index = 1

    def _swap_card(self, player: BasePlayer, card: Card) -> None:
        self._deck.append(card)
        self._shuffle_deck()
        player.cards.append(self._deck.pop())

    def _take_coin_from_treasury(self, player: BasePlayer, number_of_coins: int):
        if number_of_coins <= self._treasury:
            self._treasury -= number_of_coins
            player.coins += number_of_coins
        else:
            coins = self._treasury
            self._treasury = 0
            player.coins += coins

    def _give_coin_to_treasury(self, player: BasePlayer, number_of_coins: int):
        self._treasury += number_of_coins
        player.coins -= number_of_coins

    def _next_player(self):
        self._current_player_index = (self._current_player_index + 1) % len(self._players)
        while not self.current_player.is_active:
            self._current_player_index = (self._current_player_index + 1) % len(self._players)

    def _remove_defeated_player(self) -> Optional[BasePlayer]:
        for ind, player in enumerate(self._players):
            if not player.cards and player.is_active:
                player.is_active = False
                self._give_coin_to_treasury(player, player.coins)
                del_id = self._knowledges[ind].player.id
                self._knowledges.pop(ind)
                for i in self._knowledges:
                    self._knowledges[i].players.pop(del_id)

                return player
        return None

    def _determine_win_state(self) -> bool:
        return sum(player.is_active for player in self._players) == 1

    def _action_phase(
        self, players_without_current: list[BasePlayer],knowledgebase,play_agent
    ) -> Tuple[Action, Optional[BasePlayer]]:
        # Player chooses action
        target_action, target_player = self.current_player.choose_action(players_without_current,knowledgebase,play_agent)

        print_text(
            build_action_report_string(
                player=self.current_player, action=target_action, target_player=target_player
            ),
            with_markup=True,
        )

        return target_action, target_player

    def _challenge_against_player_failed(
        self, player_being_challenged: BasePlayer, card: Card, challenger: BasePlayer
    ):
        # Player being challenged reveals the card
        print_texts(f"{player_being_challenged} reveals their ", (f"{card}", card.style), " card!")
        print_text(f"{challenger} loses the challenge")

        # Challenge player loses influence (chooses a card to remove)
        challenger.remove_card()

        # Player puts card into the deck and gets a new card
        print_text(f"{player_being_challenged} gets a new card")
        self._swap_card(player_being_challenged, card)

    def _challenge_against_player_succeeded(self, player_being_challenged: BasePlayer):
        print_text(f"{player_being_challenged} bluffed! They do not have the required card!")

        # Player being challenged loses influence (chooses a card to remove)
        player_being_challenged.remove_card()

    def _challenge_phase(
        self,
        other_players: list[BasePlayer],
        player_being_challenged: BasePlayer,
        action_being_challenged: Union[Action, CounterAction],
        
    ) -> ChallengeResult:
        # Every player can choose to challenge
        for index,challenger in enumerate(other_players):
            should_challenge = challenger.determine_challenge(self._playerbases[self._current_player_index],str(action_being_challenged),self._knowledges[index],self._challenge_agents[index])
            if should_challenge:
                if challenger.is_ai:
                    print_text(f"{challenger} is challenging {player_being_challenged}!")
                # Player being challenged has the card
                if card := player_being_challenged.find_card(
                    action_being_challenged.associated_card_type
                ):
                    self._challenge_against_player_failed(
                        player_being_challenged=player_being_challenged,
                        card=card,
                        challenger=challenger,
                    )
                    return ChallengeResult.challenge_failed

                # Player being challenged bluffed
                else:
                    self._challenge_against_player_succeeded(player_being_challenged)
                    return ChallengeResult.challenge_succeeded

        # No challenge happened
        return ChallengeResult.no_challenge

    def _counter_phase(
        self, players_without_current: list[BasePlayer], target_action: Action
    ) -> Tuple[Optional[BasePlayer], Optional[CounterAction]]:
        # Every player can choose to counter
        for countering_player in players_without_current:
            should_counter = countering_player.determine_counter(self.current_player)
            if should_counter:
                target_counter = get_counter_action(target_action.action_type)
                print_text(
                    build_counter_report_string(
                        target_player=self.current_player,
                        counter=target_counter,
                        countering_player=countering_player,
                    )
                )

                return countering_player, target_counter

        return None, None

    def _execute_action(
        self, action: Action, target_player: BasePlayer, countered: bool = False
    ) -> None:
        match action.action_type:
            case ActionType.income:
                # Player gets 1 coin
                self._take_coin_from_treasury(self.current_player, 1)
                print_text(f"{self.current_player}'s coins are increased by 1")
            case ActionType.foreign_aid:
                if not countered:
                    # Player gets 2 coin
                    self._take_coin_from_treasury(self.current_player, 2)
                    print_text(f"{self.current_player}'s coins are increased by 2")
            case ActionType.coup:
                # Player pays 7 coin
                self._give_coin_to_treasury(self.current_player, 7)
                print_text(
                    f"{self.current_player} pays 7 coins and performs the coup against {target_player}"
                )

                if target_player.cards:
                    # Target player loses influence
                    target_player.remove_card()
            case ActionType.tax:
                # Player gets 3 coins
                self._take_coin_from_treasury(self.current_player, 3)
                print_text(f"{self.current_player}'s coins are increased by 3")
            case ActionType.assassinate:
                # Player pays 3 coin
                self._give_coin_to_treasury(self.current_player, 3)
                if not countered and target_player.cards:
                    print_text(f"{self.current_player} assassinates {target_player}")
                    target_player.remove_card()
            case ActionType.steal:
                if not countered:
                    # Take 2 (or all) coins from a player
                    steal_amount = min(target_player.coins, 2)
                    target_player.coins -= steal_amount
                    self.current_player.coins += steal_amount
                    print_text(
                        f"{self.current_player} steals {steal_amount} coins from {target_player}"
                    )
            case ActionType.exchange:
                # Get 2 random cards from deck
                cards = [self._deck.pop(), self._deck.pop()]
                first_card, second_card = self.current_player.choose_exchange_cards(cards)
                self._deck.append(first_card)
                self._deck.append(second_card)

    def handle_turn(self) -> bool:
        move_dict = {
       "player_id": "Player"+str(self._current_player_index),
        # "player_id": "Player1",
        "action": None,
        "target_id": None,
        "challenge_result": None,
        "counter_player_id": None,
        "counter_action": None,
        "counter_challenge_result": None,
        "revealed_card": None,
        "lost_card": None,
        "coins_change": 0
    }
        
        players_without_current = self._players_without_player(self.current_player)
      
         
        # Choose an action to perform
        target_action, target_player = self._action_phase(players_without_current,self._knowledges[self._current_player_index],self._play_agents[self._current_player_index])
        # rational_knowledge_dict_str = json.dumps(self._knowledges[self._current_player_index].to_dict())
        
        # inputs_play2 = {
        #     "rational_knowledge": rational_knowledge_dict_str,
        #     "intermediate_steps": []
        # }

        # out = self._play_agents[self._current_player_index].get_result(inputs_play2)
        # print(out["agent_out"])
        # print(type(out["agent_out"]))
        # output_dict = json.loads(out["agent_out"])
        
        

        move_dict["action"] = str(target_action.action_type.value)
        if target_player:
            move_dict["target_id"] = target_player.name 
        challenge_result = ChallengeResult.no_challenge
        if target_action.can_be_challenged:
            challenge_result = self._challenge_phase(
                other_players=players_without_current,
                player_being_challenged=self.current_player,
                action_being_challenged=target_action,
            )
            move_dict["challenge_result"] = challenge_result.name

        if challenge_result == ChallengeResult.challenge_succeeded:
            # Challenge succeeded and the action does not take place
            pass
        elif challenge_result == ChallengeResult.challenge_failed:
            # Challenge failed and the action is still resolved
            self._execute_action(target_action, target_player)

        elif challenge_result == ChallengeResult.no_challenge:
            # Action can't be countered
            if not target_action.can_be_countered:
                self._execute_action(target_action, target_player)

            # Opportunity to counter
            else:
                countering_player, counter = self._counter_phase(
                    players_without_current, target_action
                )
                if countering_player:
                    move_dict["counter_player_id"] = countering_player.name
                if counter:
                    move_dict["counter_action"] = str(counter.counter_type.value)

                # Opportunity to challenge counter
                counter_challenge_result = ChallengeResult.no_challenge
                if countering_player and counter:
                    players_without_countering_player = self._players_without_player(
                        countering_player
                    )
                    counter_challenge_result = self._challenge_phase(
                        other_players=players_without_countering_player,
                        player_being_challenged=countering_player,
                        action_being_challenged=counter,
                    )
                    move_dict["counter_challenge_result"] = counter_challenge_result.name

                # Successfully countered and counter not challenged
                if counter and counter_challenge_result in [
                    ChallengeResult.no_challenge,
                    ChallengeResult.challenge_failed,
                ]:
                    self._execute_action(target_action, target_player, countered=True)
                # No counter occurred
                else:
                    self._execute_action(target_action, target_player)

        # Is any player out of the game?
        while player := self._remove_defeated_player():
            if player.is_ai:
                print_text(f"{player} was defeated! :skull: :skull: :skull:", with_markup=True)
            else:
                # Our human was defeated
                print_text("You were defeated! :skull: :skull: :skull:", with_markup=True)
                end_game = print_confirm("Do you want to end the game early?")
                if end_game:
                    return True

        # Have we reached a winner?
        if self._determine_win_state():
            print_text(
                f":raising_hands: Congratulations {self.remaining_player}! You are the final survivor!",
                with_markup=True,
            )
            return True
        if target_action.action_type in [ActionType.income, ActionType.foreign_aid, ActionType.tax]:
            move_dict["coins_change"] = f"{self.current_player.coins}"
        
    
       
        # No winner yet
        
        for i in range(len(self._knowledges)):
            if i ==self._current_player_index:
                # print("^"*80)
                # print(self._knowledges[i])
                updated_cards = [str(card) for card in self._players[i].cards]

                self._knowledges[i].update_after_move(move_dict,True)
                self._knowledges[i].own_cards = updated_cards
                # print("^"*80)
                # print(self._knowledges[i])
                # print("^"*80)
            else:
                # print(self._knowledges[i])
                updated_cards = [str(card) for card in self._players[i].cards]
                self._knowledges[i].update_after_move(move_dict,False)
                self._knowledges[i].own_cards = updated_cards
                # print("^"*80)
                # print(self._knowledges[i])
        

      

        
      
        self._next_player()
        # mom = PlayerBase(id="P1", name="Mom", coins=2, prompt_str="Mom is a gullible and innocent player, often easily convinced by others.", details="Mom is known for her trusting nature and tendency to believe in the good of others.", tags=["gullible", "innocent"], numberofcards=2, alive=True, probability_to_bluff=0.1, current_quote="I don't think you should challenge me on this!")

        # dad = PlayerBase(id="P2", name="Dad", coins=2, prompt_str="Dad is a charismatic and charming player, who enjoys the art of persuasion. His bluffs are incredibly convincing, making it difficult for others to discern his true intentions. He thrives on the challenge of outwitting his opponents through deception and psychological tactics.", details="Dad has an extensive understanding of game dynamics and psychology, frequently studying bluffing techniques and tactics, making him a master of misinformation. His preferred cards are Duke and Assassin, and his favorite actions are claiming to be Duke or Assassin, challenging other players' claims, and taking risky actions based on bluffs.", tags=["charismatic", "charming", "persuasive"], numberofcards=2, alive=True, probability_to_bluff=0.9, current_quote="I assure you, I'm the Duke. Anyone who doubts me will regret it.")


        # own_cards = ['Duke', 'Assassin']
        # rational_knowledge = RationalPlayerKnowledge(player=dad, total_players=3, players=[mom], own_cards=own_cards)

        # rational_knowledge_dict_str = json.dumps(rational_knowledge.to_dict())

        # inputs_play = {
        #     "rational_knowledge": rational_knowledge_dict_str,
        #     "intermediate_steps": []
        # }
        # out = self._play_agents[0].get_result(inputs_play)
        # print(out["agent_out"])
        hi= input("buffer: ")
        return False

