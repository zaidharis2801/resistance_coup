class PlayerBase:
    def __init__(self, id, name, coins, prompt_str, details, tags, numberofcards, alive, probability_to_bluff, current_quote):
        self.id = id
        self.name = name
        self.coins = coins
        self.prompt_str = prompt_str
        self.details = details
        self.tags = tags
        self.numberofcards = numberofcards
        self.alive = alive
        self.past_actions = []
        self.probability_to_bluff = probability_to_bluff
        self.current_quote = current_quote

    def __str__(self):
        return (f"Player ID: {self.id}\n"
                f"Name: {self.name}\n"
                f"Coins: {self.coins}\n"
                f"Prompt: {self.prompt_str}\n"
                f"Details: {self.details}\n"
                f"Tags: {', '.join(self.tags)}\n"
                f"Number of Cards: {self.numberofcards}\n"
                f"Alive: {'Yes' if self.alive else 'No'}\n"
                f"Past Actions: {', '.join(self.past_actions)}\n"
                f"Probability to Bluff: {self.probability_to_bluff}\n"
                f"Current Quote: {self.current_quote}")
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "coins": self.coins,
            "prompt_str": self.prompt_str,
            "details": self.details,
            "tags": self.tags,
            "numberofcards": self.numberofcards,
            "alive": self.alive,
            "past_actions": self.past_actions,
            "probability_to_bluff": self.probability_to_bluff,
            "current_quote": self.current_quote
        }


