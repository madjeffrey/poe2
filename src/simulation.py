from game import Game
from Players.player import Player
import time
import random

# made simulation class so that the player is able to know if it is his turn, also improves generalizability
# also was able to have settings to see if we want iterations or infinite
# but due to having a new quality to check if it is a new game, the player order does not matter for now

class Simulation:
    """
    Question: 
    [x] should the simulation handle the recording of games, or have the game record itself
    - game should record itself to allow the simulation to handle any 2 player games


    todo:
    [x] have setter for mirror match, recordGames, recordStats
    [ ] store the dictionary for many runs and then update them every once in a while say every 1000 runs
    """
    def __init__(self, startBoard:tuple, p1:Player, p2:Player, iterations:int=0, settings:tuple=(False, True, True, True, 0)):
        """
        Args:
            startBoard(numRows, numCols, scoreCutoff, handicap)
            p1 must be an object of subclass of Player
            p2 must be an object of subclas of Player
            iterations: 0 -> inf else n interations
            settings:(printGame, recordStats, recordGames, ignoreMirrorMatch, delay(in seconds))
        """

        # initialize gameSettings
        self.__iterations = iterations
        self.__printGame = settings[0]
        self.__settings = settings
        self.__delay = settings[4]
        self.__p1 = p1
        self.__p2 = p2
        self.__startBoard = startBoard

        
    def run(self):
        # if iterations = 0 then go for infinity, if iterations does not equal 0 then go until count = iterations
        count = 0
        while not self.__iterations or count < self.__iterations:
            # randomly flit which player goes first or second
            # fixed error of before the update paths for who went first or second would be wrong
            num = random.random()
            if num < 0.5:
                tmp = self.__p1
                self.__p1 = self.__p2
                self.__p2 = tmp

            # create a new game of the same type and settings
            self.__game = Game(self.__startBoard[0], self.__startBoard[1], self.__startBoard[2], self.__startBoard[3], self.__p1.getClassPath(), self.__p2.getClassPath())
            self.__game.setRecordStats(self.__settings[1])
            self.__game.setRecordGames(self.__settings[2])
            self.__game.setIgnoreMirrorMatch(self.__settings[3])
        
            # give the players references to the game and set their order since it is a new game
            self.__p1.setGame(self.__game, 1)
            self.__p2.setGame(self.__game, 2)

            # run an episode
            while not self.__game.gameOver():
                if self.__printGame:
                    print(self.__p1.actionMove(), "p1")
                    print(self.__game)
                    time.sleep(self.__delay)
                    if not self.__game.gameOver():
                        print(self.__p2.actionMove(), "p2")
                        print(self.__game)
                        time.sleep(self.__delay)
                else:
                    self.__p1.actionMove()
                    if not self.__game.gameOver():
                        self.__p2.actionMove()

            self.__game.save()
            count += 1