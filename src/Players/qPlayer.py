from player import Player
from game import Game
import random

class QPlayer(Player):
    def __init__(self, name='qBot', _qTable={}):
        super().__init__(name)
        self._qTable = _qTable  # Q-table for storing state-action values
        self._storePath = './qPlayerStore/'

    

    def setGame(self, game:Game, order:int):
        """
        sets a reference to the game, as well as the player order
        """
        self._game = game
        self._playerOrder = order
        self._hash = 0
        self._

    def choose_action(self, state, epsilon):
        import random
        if random.uniform(0, 1) < epsilon:
            # Explore: choose a random action
            action = random.choice(self.get_possible_actions(state))
        else:
            # Exploit: choose the best action from Q-table
            action = self.get_best_action(state)
        return action

    def get_best_action(self, state):
        possible_actions = self.get_possible_actions(state)
        q_values = [self._qTable.get((state, action), 0) for action in possible_actions]
        max_q_value = max(q_values)
        best_actions = [action for action, q in zip(possible_actions, q_values) if q == max_q_value]
        return random.choice(best_actions)

    def update_q_value(self, state, action, reward, next_state, alpha, gamma):
        current_q = self._qTable.get((state, action), 0)
        next_max_q = max([self._qTable.get((next_state, a), 0) for a in self.get_possible_actions(next_state)], default=0)
        new_q = current_q + alpha * (reward + gamma * next_max_q - current_q)
        self._qTable[(state, action)] = new_q


    def saveState(self):
        __stats = None
        if path:
            __pClass = path.split("/")[-1].removesuffix(".json")
            # if the file does not exist make the file
            if not os.path.exists(path):
                with open(path, "w") as file:
                    # check if the file is empty, if so create a new dict
                    __stats = {"class": __pClass, "gamesPlayed": 0, "gamesWon": 0, "gamesLost":0, "gamesWonAsP1": 0, "gamesWonAsP2":0, "winningVS" : { oppClass : { "gamesPlayed" : 0, "gamesWon":0, "gamesLost":0, "gamesWonAsP1": 0, "gamesWonAsP2":0, "gamesList":[] } } }
                    json.dump(__stats, file)
            
            # open the file to read than write 
            with open(path, "r+") as file:
                __stats = json.load(file)
                # update the stats for the game just played
                __stats["gamesPlayed"] += 1
                # check if first time facing opponent if so initialize key
                if oppClass not in __stats["winningVS"].keys():
                    __stats["winningVS"][oppClass] = { "gamesPlayed" : 0, "gamesWon":0, "gamesLost":0, "gamesWonAsP1": 0, "gamesWonAsP2":0, "gamesList":[] }
                
                __stats["winningVS"][oppClass]["gamesPlayed"] = 1 + __stats["winningVS"][oppClass]["gamesPlayed"]
                if self.__won == playerOrder:
                    __stats["gamesWon"] += 1
                    __stats[f"gamesWonAsP{playerOrder}"] += 1
                    __stats["winningVS"][oppClass]["gamesWon"] += 1
                    __stats["winningVS"][oppClass][f"gamesWonAsP{playerOrder}"] += 1
                else:
                    assert self.__won != 0, "there is no winner when there should be"
                    __stats["gamesLost"] += 1
                    __stats["winningVS"][oppClass]["gamesLost"] += 1
                
                if self.__recordGames:
                    __stats["winningVS"][oppClass]["gamesList"].append(self.__id)
                file.seek(0)
                json.dump(__stats, file)
                file.truncate()