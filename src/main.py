from game import Game
from Players.player import Player
from Players.randomPlayer import RandomPlayer
from Players.clusterPlayer import ClusterPlayer
from Players.friendlyNeighborPlayer import FriendlyNeighborPlayer 
import time
import random

"""
Question: 
[] should the simulation handle the recording of games, or have the game record itself
todo:
[x] have setter for mirror match, recordGames, recordStats
"""
# made simulation class so that the player is able to know if it is his turn, also improves generalizability
# also was able to have settings to see if we want iterations or infinite
# but due to having a new quality to check if it is a new game, the player order does not matter for now

class Simulation:
    def __init__(self, startBoard:tuple, p1:Player, p2:Player, iterations:int=0, settings:tuple=(False, True, True, True, 0)):
        """
        args:
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


if __name__ == "__main__":
    # rules for main
    delay = 0
    printGame = False
    
    # set rules for the game
    rows = 10
    cols = 10
    cutoff = 0
    handicap = 0.5
    
    # initialize the players
    randPlayer = RandomPlayer()
    CluPlayer = ClusterPlayer()
    cluPlayer = ClusterPlayer()
    friendlyPlayer = FriendlyNeighborPlayer()
    

    # it is saving more games than the limit says, maybe i just didn't save the main file before setting it to 50000
    #                                                                            printGame, recordStats, recordGame, ignoreMirror, delay
    sim = Simulation((rows, cols, cutoff, handicap), friendlyPlayer, randPlayer, 5000, (False, True, True, False, 0))
    sim.run()



