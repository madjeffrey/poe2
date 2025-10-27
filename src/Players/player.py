from game import Game
import json
import os

class Player:
    """
    This is a template super class for a given player that will implement a given stategy
    it must update the function actionMove() returning the coordinates of its next move

    the description must describe the strategy of the player
    the class path holds the path to the json file of the stats for a given player strategy
    if the player wishes to know the game state it must do it in its initialization
    """

    
    def __init__(self, name="bot"):
        self._game = None
        self._name = name
        self._playerOrder = 0
        self._row = -69 # current estimate of next move
        self._col = -69 # current estimate of next move
        self._classPath = "../statistics/classes/" + str(self.__class__).split(".")[-1].replace("'>", ".json")
        self.initStats()
        assert self._desc, "class does not have a description"

    def initStats(self)->dict:
        """
        creates a dictionary or pulls it if it exists
        """
        # if the file does not exist make the file
        if not os.path.exists(self._classPath):
            with open(self._classPath, "w") as file:
                # check if the file is empty, if so create a new dict
                self._stats = {"class": type(self).__name__, "gamesPlayed": 0, "gamesWon": 0, "gamesLost":0, "gamesWonAsP1": 0, "gamesWonAsP2":0, "winningVS" : {} }
                json.dump(self._stats, file)
        else:
            with open(self._classPath, "r+") as file:
                self._stats = json.load(file)

    def getClassPath(self):
        """
        returns:
            the file path to the class for statistics
        """
        return self._classPath

    def getPlayerOrder(self):
        """
        returns:
            if player is unassigned: 0, player 1: 1 or player 2: 2
        """
        return self._playerOrder
    
    def setGame(self, game:Game, order:int):
        """
        sets a reference to the game, as well as the player order
        """
        self._game = game
        self._playerOrder = order

    def isTestable(self):
        return False

    def actionMove(self)->tuple:
        """
        required implementation for subclass
        
        returns: 
            tuple of move played
            (-69, -69) means not implemented
            Player only needs to know about the game here, and not at initialization
        """
        assert self._game, "no game found: cannot make a move"
        return (self._row, self._col)
    
    def __str__(self):
        return f"Hello I am player {self.__name}, my strategy is: {self.__desc}"
    

