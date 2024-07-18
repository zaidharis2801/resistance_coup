class CoupGame:
    def __init__(self, r, n, Pc_Duke, Pc_Contessa, Pc_Captain, Pc_Ambassador, gold_coins, cards):
        self.r = r
        self.n = n
        self.Pc_Duke = Pc_Duke
        self.Pc_Contessa = Pc_Contessa
        self.Pc_Captain = Pc_Captain
        self.Pc_Ambassador = Pc_Ambassador
        self.gold_coins = gold_coins
        self.cards = cards

    def calculate_win_points(self):
        return 1000

    def calculate_lose_points(self):
        return -1000

    def calculate_lose_card_points(self):
        return -500

    def calculate_enemy_lose_card_points(self):
        return 500 / self.r

    def calculate_gold_coin_points(self):
        return self.gold_coins * 70

    def calculate_eliminate_enemy_points(self):
        return 1000 / self.r

    def calculate_income_points(self):
        return 70

    def calculate_foreign_aid_points(self):
        return 140 * (1 - self.Pc_Duke)

    def calculate_coup_points(self):
        return (500 - 500) / self.n

    def calculate_duke_points(self):
        return 210

    def calculate_assassin_points_not_eliminating(self):
        return 500 * (1 - self.Pc_Contessa) - 210

    def calculate_assassin_points_eliminating(self):
        return (1000 / self.r) * (1 - self.Pc_Contessa) - 210

    def calculate_captain_points(self):
        return 140 + 140 * (1 - (self.Pc_Captain + self.Pc_Ambassador))

    def calculate_all_points(self):
        points = {
            "Income": self.calculate_income_points(),
            "Foreign Aid": self.calculate_foreign_aid_points(),
            "Coup": self.calculate_coup_points(),
        }
       
        points["Tax"] = self.calculate_duke_points()
        
        not_eliminating=self.calculate_assassin_points_not_eliminating()
        eliminating=self.calculate_assassin_points_eliminating()
        points["Assassinate"] = max(not_eliminating,eliminating)
         
        
        points["Steal"] = self.calculate_captain_points()
        return points

    def get_best_action(self):
        actions_points = self.calculate_all_points()
        best_action = max(actions_points, key=actions_points.get)
        return best_action, actions_points[best_action]