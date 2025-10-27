from game import Game
from Players.player import Player
from Players.randomPlayer import RandomPlayer
from Players.clusterPlayer import ClusterPlayer
from Players.friendlyNeighborPlayer import FriendlyNeighborPlayer 
from simulation import Simulation
import time
import random

class TestRun(Simulation):
    def __init__(self, startBoard:tuple, p1:Player, p2:Player, iterations:int=0, settings:tuple=(False, True, True, True, 0, 10000)):
        """
        Args:
            startBoard(numRows, numCols, scoreCutoff, handicap)
            p1 must be an object of subclass of Player
            p2 must be an object of subclas of Player
            iterations: 0 -> inf else n interations
            settings:(printGame, recordStats, recordGames, ignoreMirrorMatch, delay(in seconds))
        """
        super().__init__(startBoard, p1, p2, iterations, settings)

    def run(self):
        # if iterations = 0 then go for infinity, if iterations does not equal 0 then go until count = iterations
        count = 0
        assert self._p1.isTestable() and self._p2.isTestable(), f'one of the players is not testable, p1:{self._p1}, p2: {self._p2}'
        while not self._iterations or count < self._iterations:
            # randomly flit which player goes first or second
            # fixed error of before the update paths for who went first or second would be wrong
            num = random.random()
            if num < 0.5:
                tmp = self._p1
                self._p1 = self._p2
                self._p2 = tmp

            # create a new game of the same type and settings
            self._game = Game(self._startBoard[0], self._startBoard[1], self._startBoard[2], self._startBoard[3])
            self._game.setRecordStats(self._settings[1])
            self._game.setRecordGames(self._settings[2])
            self._game.setIgnoreMirrorMatch(self._settings[3])

        
            # give the players references to the game and set their order since it is a new game
            self._p1.setGame(self._game, 1)
            self._p2.setGame(self._game, 2)

            # set the seed making sure we have the right classes
            self._p1.setSeed(count+3)
            self._p2.setSeed(count+5)


            # run an episode
            while not self._game.gameOver():
                if self._printGame:
                    # print the type of the players then the game
                    print(f"p1: {type(self._p1)} | p2: {type(self._p2)}")
                    print(self._p1.actionMove(), "p1")
                    self._runTest()
                    print(self._game)
                    time.sleep(self._delay)
                    if not self._game.gameOver():
                        # print the type of the players then the game
                        print(f"p1: {type(self._p1)} | p2: {type(self._p2)}")
                        print(self._p2.actionMove(), "p2")
                        self._runTest()
                        print(self._game)
                        time.sleep(self._delay)
                else:
                    self._p1.actionMove()
                    self._runTest()
                    if not self._game.gameOver():
                        self._p2.actionMove()
                        self._runTest()

            if self._recordStatistics:
                self._saveGame()
                if not (count+1)%self._recordInterval:
                    self._savePlayerStats()
            count += 1


    def _runTest(self):
        """
        run tests
        """
        self._scoreTest()


    def _scoreTest(self):
        """
        after a move is played check if the scores are the same
        """
        linearScore = self._game.getPlayerScores()
        exponentialScore = self._game.calcScoreSlow()
        assert linearScore == exponentialScore, f'\n****************************\nTest Failed: scores are not the same\nlinearScore: {linearScore}\nexponentialScore: {exponentialScore}\n{str(self._game)}\n{self._game.getMoveHistory()}\n****************************\n'