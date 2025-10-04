from player import Player
from game import Game
import random as rand

class RandomPlayer(Player):
    def __init__(self):
        self._desc = "This player will always take a random legal action given the dimensions of the board"
        super().__init__()

    def __init__(self, name):
        self._desc = "This player will always take a random legal action given the dimensions of the board"
        super().__init__(name)
    
    # def getClassPath(self):
    #     return super()._classPath

    def actionMove(self, game:Game)->bool:
        """
        return True if move was successfully played
        """
        # will this be an updated version of the game, if not just call it with the game before it makes a decision
        # am I able to update the game state from within this function
        while True:
            init = game.getInit()
            randRow = rand.randint(0, init[0]-1)
            randCol = rand.randint(0, init[1]-1)
            if game.isLegal(randRow, randCol):
                game.playMove(randRow, randCol)
                return (randRow, randCol)
