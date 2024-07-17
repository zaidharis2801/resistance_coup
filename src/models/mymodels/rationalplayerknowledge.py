class RationalPlayerKnowledge:
    def __init__(self, player, total_players, players, own_cards):
        self.player = player
        self.total_players = total_players
        self.players = {p.id: p for p in players}
        self.own_cards = own_cards
        self.revealed_cards = []
        self.actions_taken = []
        self.plays_made=[]
        self.claims = {p.id: [] for p in players}
        self.challenges = []
        self.blocked_actions = []
        self.card_counts = {
            'Duke': 3,
            'Assassin': 3,
            'Captain': 3,
            'Ambassador': 3,
            'Contessa': 3
        }
        self.coins = {p.id: 2 for p in players}  # Assuming starting coins for all players is 2
        self.players_except_self = [p for p in players if p.id != player.id]

        for card in own_cards:
            self.card_counts[card] -= 1
        self.unknown_cards = sum(self.card_counts.values()) - len(self.own_cards)

    def __str__(self):
        return (f"Player: {self.player}\n"
                f"Total Players: {self.total_players}\n"
                f"Players: {', '.join(str(p) for p in self.players.values())}\n"
                f"Own Cards: {self.own_cards}\n"
                f"Revealed Cards: {self.revealed_cards}\n"
                f"Actions Taken: {self.actions_taken}\n"
                f"Claims: {self.claims}\n"
                f"Challenges: {self.challenges}\n"
                f"Blocked Actions: {self.blocked_actions}\n"
                f"Card Counts: {self.card_counts}\n"
                f"Unknown Cards: {self.unknown_cards}\n"
                f"Coins: {self.coins}")

    def to_dict(self):
        return {
            "player": self.player.to_dict(),
            "total_players": self.total_players,
            "players": {id: player.to_dict() for id, player in self.players.items()},
            "own_cards": self.own_cards,
            "revealed_cards": self.revealed_cards,
            "actions_taken": self.actions_taken,
            "claims": {id: claims for id, claims in self.claims.items()},
            "challenges": self.challenges,
            "blocked_actions": self.blocked_actions,
            "card_counts": self.card_counts,
            "unknown_cards": self.unknown_cards,
            "coins": self.coins
        }

    def update_after_move(self, move, is_current_player):
        player_id = move["player_id"]
        action = move["action"]
        target_id = move.get("target_id")
        challenge_result = move.get("challenge_result")
        counter_player_id = move.get("counter_player_id")
        counter_action = move.get("counter_action")
        counter_challenge_result = move.get("counter_challenge_result")
        revealed_card = move.get("revealed_card")
        lost_card = move.get("lost_card")
        coins_change = move.get("coins_change")

        # Update coins
        if coins_change:
            self.coins[player_id] = int(coins_change)  # Updated to set the new coins value

        # Track actions
        self.actions_taken.append(move)
        self.plays_made.append((player_id,action))

        # Update claims
        if action:
            self.claims[player_id].append(action)

        # Update challenges
        if challenge_result:
            self.challenges.append({"challenger": player_id, "result": challenge_result})

        # Update blocked actions
        if counter_action:
            self.blocked_actions.append({"blocker": counter_player_id, "blocked": counter_action})

        # Update revealed cards
        if revealed_card:
            self.revealed_cards.append({"player_id": player_id, "card": revealed_card})
            self.card_counts[revealed_card] -= 1
            self.unknown_cards -= 1

        # If a card is lost, remove it from the player's knowledge
        if lost_card:
            if lost_card in self.own_cards:
                self.own_cards.remove(lost_card)
            self.card_counts[lost_card] += 1
            self.unknown_cards += 1
