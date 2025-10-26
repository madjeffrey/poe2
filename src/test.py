from game import Game
from Players.player import Player
from Players.randomPlayer import RandomPlayer
from Players.clusterPlayer import ClusterPlayer
from Players.friendlyNeighborPlayer import FriendlyNeighborPlayer 
from simulation import Simulation
import time
import random

class testRun(Simulation):
    def __init__(startBoard:tuple, p1:Player, p2:Player, iterations:int=0, settings:tuple=(False, True, True, True, 0)):
        """
        Args:
            startBoard(numRows, numCols, scoreCutoff, handicap)
            p1 must be an object of subclass of Player
            p2 must be an object of subclas of Player
            iterations: 0 -> inf else n interations
            settings:(printGame, recordStats, recordGames, ignoreMirrorMatch, delay(in seconds))
        """
        super.__init__(startBoard, p1, p2, iterations, settings)

    def run(self):
        # if iterations = 0 then go for infinity, if iterations does not equal 0 then go until count = iterations
        count = 0
        assert self.__p1.isTestable() and self.__p2.isTestable(), 'one of the players is not testable'
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

            # set the seed making sure we have the right classes
            self.__p1.setSeed(count+3)
            self.__p2.setSeed(count+5)


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
                    self.__runTest()
                    if not self.__game.gameOver():
                        self.__p2.actionMove()
                        self.__runTest()

            self.__game.save()
            count += 1


    def __runTest(self):
        """
        run tests
        """
        self.__scoreTest()


    def __scoreTest(self):
        """
        after a move is played check if the scores are the same
        """
        linearScore = self.__game.getPlayerScores()
        exponentialScore = self.__game.calcScoreSlow()
        assert linearScore == exponentialScore, f'\n****************************\nTest Failed: scores are not the same\nlinearScore: {linearScore}\nexponentialScore: {exponentialScore}\n{str(self.__game)}\n{self.__game.getMoveHistory()}\n****************************\n'