from Players.player import Player
from game import Game
import random as rand

class RandomPlayer(Player):
    def __init__(self, name="randomBot"):
        self._desc = "This player will always take a random legal action given the dimensions of the board"
        super().__init__(name)
    

    def actionMove(self)->tuple:
        """
        returns:
            True if move was successfully played
        """
        # will this be an updated version of the game, if not just call it with the game before it makes a decision
        # am I able to update the game state from within this function
        assert self._game, "no game: set the game"
        while True:
            init = self._game.getInit()
            self._row = rand.randint(0, init[0]-1)
            self._col = rand.randint(0, init[1]-1)
            if self._game.isLegal(self._row, self._col):
                self._game.playMove(self._row, self._col)
                return (self._row, self._col)
