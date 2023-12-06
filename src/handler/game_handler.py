import random
from enum import Enum
from typing import List, Optional, Tuple, Union

import names

from src.models.action import (
    Action,
    ActionType,
    CounterAction,
    CounterActionType,
    get_counter_action,
)
from src.models.card import Card, create_deck
from src.models.players.ai import AIPlayer
from src.models.players.base import BasePlayer
from src.models.players.human import HumanPlayer
from src.utils.print import (
    print_blank,
    print_confirm,
    print_table,
    print_text,
    print_texts,
)
from src.utils.table import generate_table


class ChallengeResult(Enum):
    no_challenge = 0
    challenge_failed = 1
    challenge_succeeded = 2


def _build_action_report_string(
    player: BasePlayer, action: Action, target_player: BasePlayer
) -> str:
    action_report_string = f"{player} chose to "
    match action.action_type:
        case ActionType.income:
            action_report_string += "take income. Their coins are increased by 1."
        case ActionType.foreign_aid:
            action_report_string += "take foreign aid. Their coins are increased by 2."
        case ActionType.coup:
            action_report_string += (
                f"perform a coup against {target_player.name}. They pay 7 coins."
            )
        case ActionType.tax:
            action_report_string += "take tax because they have influence over a Duke."
        case ActionType.assassinate:
            action_report_string += f"assassinate {target_player.name}."
        case ActionType.steal:
            action_report_string += f"steal coin from {target_player.name}"
        case ActionType.exchange:
            action_report_string += (
                "perform an exchange, because they have influence over an Ambassador."
            )

    return action_report_string


def _build_counter_report_string(
    target_player: BasePlayer, counter: CounterAction, countering_player: BasePlayer
) -> str:
    counter_report_string = f"{countering_player} chose to "
    match counter.counter_type:
        case CounterActionType.block_foreign_aid:
            counter_report_string += f"block {target_player}'s attempt to take foreign aid."
        case CounterActionType.block_assassination:
            counter_report_string += f"block {target_player}'s assassination attempt."
        case CounterActionType.block_steal:
            counter_report_string += f"block {target_player} from stealing."

    return counter_report_string


class ResistanceCoupGameHandler:
    _players: List[BasePlayer] = []
    _current_player_index = 0
    _deck: List[Card] = []
    _number_of_players: int = 0
    _treasury: int = 0

    def __init__(self, player_name: str, number_of_players: int):
        self._number_of_players = number_of_players

        # Set up players
        self._players.append(HumanPlayer(name=player_name))

        unique_names = set()
        for i in range(number_of_players - 1):
            gender = random.choice(["male", "female"])

            ai_name = names.get_first_name(gender=gender)
            while ai_name in unique_names:
                ai_name = names.get_first_name(gender=gender)

            unique_names.add(ai_name)

            self._players.append(AIPlayer(name=ai_name))

    @property
    def current_player(self) -> BasePlayer:
        return self._players[self._current_player_index]

    def print_players(self) -> None:
        print_blank()
        print_table(generate_table(self._players, self._current_player_index))
        print_blank()

    def _players_without_player(self, excluded_player: BasePlayer):
        players_copy = self._players.copy()
        return [
            player
            for player in players_copy
            if player.is_active and player.name != excluded_player.name
        ]

    def _shuffle_deck(self) -> None:
        random.shuffle(self._deck)

    def reset_game(self) -> None:
        self._deck = create_deck()
        self._shuffle_deck()

        self._treasury = 50 - 2 * len(self._players)

        for player in self._players:
            player.reset_player()

            # Deal 2 cards to each player
            player.cards.append(self._deck.pop())
            player.cards.append(self._deck.pop())

            # Gives each player 2 coins
            player.coins = 2

            # Includes the player in the game
            player.is_active = True

        # Random starting player
        self._current_player_index = random.randint(0, self._number_of_players - 1)

    def _swap_card(self, player: BasePlayer, card: Card) -> None:
        self._deck.append(card)
        self._shuffle_deck()
        player.cards.append(self._deck.pop())

    def _take_coin_from_treasury(self, number_of_coins: int):
        if number_of_coins <= self._treasury:
            self._treasury -= number_of_coins
            self.current_player.coins += number_of_coins
        else:
            coins = self._treasury
            self._treasury = 0
            self.current_player.coins += coins

    def _give_coin_to_treasury(self, number_of_coins: int):
        self._treasury += number_of_coins
        self.current_player.coins -= number_of_coins

    def _next_player(self):
        self._current_player_index = (self._current_player_index + 1) % len(self._players)
        while not self.current_player.is_active:
            self._current_player_index = (self._current_player_index + 1) % len(self._players)

    def _action_phase(
        self, players_without_current: list[BasePlayer]
    ) -> Tuple[Action, Optional[BasePlayer]]:
        # Player chooses action
        target_action, target_player = self.current_player.choose_action(players_without_current)

        print_blank()
        print_text(
            _build_action_report_string(
                player=self.current_player, action=target_action, target_player=target_player
            )
        )

        return target_action, target_player

    def _challenge_against_player_failed(
        self, player_being_challenged: BasePlayer, card: Card, challenger: BasePlayer
    ):
        # Player being challenged reveals the card
        print_blank()
        print_texts(f"{player_being_challenged} reveals their ", (f"{card}", card.style), " card!")

        # Challenge player loses influence (chooses a card to remove)
        challenger.remove_card()

        # Player puts card into the deck and gets a new card
        self._swap_card(player_being_challenged, card)

    def _challenge_against_player_succeeded(self, player_being_challenged: BasePlayer):
        print_blank()
        print_text(f"{player_being_challenged} does not have the required card!")

        # Player being challenged loses influence (chooses a card to remove)
        player_being_challenged.remove_card()

    def _challenge_phase(
        self,
        other_players: list[BasePlayer],
        player_being_challenged: BasePlayer,
        action_being_challenged: Union[Action, CounterAction],
    ) -> ChallengeResult:
        # Every player can choose to challenge
        for challenger in other_players:
            should_challenge = challenger.determine_challenge(player_being_challenged)
            if should_challenge:
                if challenger.is_ai:
                    print_blank()
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
                print_blank()
                print_text(
                    _build_counter_report_string(
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
                self._take_coin_from_treasury(1)
            case ActionType.foreign_aid:
                if not countered:
                    # Player gets 2 coin
                    self._take_coin_from_treasury(2)
            case ActionType.coup:
                # Player pays 7 coin
                self._give_coin_to_treasury(7)

                # Target player loses influence
                target_player.remove_card()
            case ActionType.tax:
                # Player gets 3 coins
                self._take_coin_from_treasury(3)
            case ActionType.assassinate:
                # Player pays 7 coin
                self._give_coin_to_treasury(3)
                if not countered:
                    target_player.remove_card()
            case ActionType.steal:
                if not countered:
                    # Take 2 (or all) coins from a player
                    steal_amount = min(target_player.coins, 2)
                    target_player.coins -= steal_amount
                    self.current_player.coins += steal_amount
            case ActionType.exchange:
                # Get 2 random cards from deck
                cards = [self._deck.pop(), self._deck.pop()]
                first_card, second_card = self.current_player.choose_exchange_cards(cards)
                self._deck.append(first_card)
                self._deck.append(second_card)

    def _remove_defeated_player(self) -> BasePlayer:
        for ind, player in enumerate(self._players):
            if not player.cards and player.is_active:
                player.is_active = False

                self._treasury += player.coins
                player.coins = 0

                return player

    def _determine_win_state(self) -> bool:
        return sum(player.is_active for player in self._players) == 1

    def handle_turn(self) -> bool:
        players_without_current = self._players_without_player(self.current_player)

        # Choose an action to perform
        target_action, target_player = self._action_phase(players_without_current)

        # Opportunity to challenge action
        challenge_result = ChallengeResult.no_challenge
        if target_action.can_be_challenged:
            challenge_result = self._challenge_phase(
                other_players=players_without_current,
                player_being_challenged=self.current_player,
                action_being_challenged=target_action,
            )

        # Action can't be countered
        if not target_action.can_be_countered:
            self._execute_action(target_action, target_player)

        # No challenge occurred, counter can still happen
        if challenge_result == ChallengeResult.no_challenge:
            # Opportunity to counter
            countering_player, counter = self._counter_phase(players_without_current, target_action)

            # Opportunity to challenge counter
            counter_challenge_result = ChallengeResult.no_challenge
            if countering_player and counter:
                players_without_countering_player = self._players_without_player(countering_player)
                counter_challenge_result = self._challenge_phase(
                    other_players=players_without_countering_player,
                    player_being_challenged=countering_player,
                    action_being_challenged=counter,
                )

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
        if player := self._remove_defeated_player():
            # Our human was defeated
            if player.is_ai:
                print_blank()
                print_text(f"{player} was defeated! :skull: :skull: :skull:", with_markup=True)
            else:
                print_text("You were defeated! :skull: :skull: :skull:", with_markup=True)
                end_game = print_confirm("Do you want to end the game early?")
                if end_game:
                    return True

        # Have we reached a winner?
        if self._determine_win_state():
            print_text(
                f":raising_hands: Congratulations {self.current_player}! You are the final survivor!",
                with_markup=True,
            )
            return True

        # Move index to next player
        self._next_player()

        # No winner yet
        return False