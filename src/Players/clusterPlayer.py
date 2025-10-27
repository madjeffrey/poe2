from Players.player import Player
from game import Game
import random

"""
Questions: is it more efficient to pass a reference to the board in once, and then can still access the board, or will this board but out of date to the current state of the board
it definitely is and so I will implement it
"""

class ClusterPlayer(Player):
    def __init__(self, name="clusterBot"):
        self._desc = "This player will always take a random legal action with the least number of empty adjacent cells given the dimensions of the board"
        super().__init__(name)
        self.__first = True
        self.__seed = 0 
        
    # override testable
    def isTestable(self):
        return True

    def setSeed(self, seed:int):
        self.__seed = seed

    def actionMove(self)->tuple:
        """
        return the move played
        """
        assert self._game, "no game: set the game"
        assert self._game.getCurrentPlayer() == self._playerOrder, f"ERROR: not player {self._playerOrder}'s turn, but tries to play"

        if self.__first:
            self.__first = False
            self.__startState = self._game.getInit()
            self.__clusterBoard= [[0]*self.__startState[1] for _ in range(self.__startState[0])]

        # if no stones on the board take the center
        if self._game.getIsNewGame():
            self._row = self.__startState[0]//2
            self._col = self.__startState[1]//2
            self._game.playMove(self._row, self._col)
            self._updateClusters(self._row, self._col)
            return (self._row, self._col)


        # update the cluster with the other players move
        moveHistory = self._game.getMoveHistory()[0] # this is good because it doesn't allow poping so therefore I am not changing the state
        fullMove = moveHistory[-1]
        move = fullMove[0]
        self._updateClusters(move[0],move[1])
        # sets the row and col to the legal move with the max num of neighbors
        self._maxClusterPos()
        # play the move
        self._game.playMove(self._row, self._col)
        # update my neighbors 
        self._updateClusters(self._row, self._col)

        ## this can always be the case because it is the global variables for the current estimated move
        return (self._row, self._col)


    def _updateClusters(self, row:int, col:int)->None:
        # assert proper row and col is given
        assert 0 <= row < self.__startState[0], "row is out of bounds"
        assert 0 <= col < self.__startState[1], "col is out of bounds"
        # update vertical neighbors
        self._updateLineCluster(row, col, 1, 0)
        # update horizontal neighbors
        self._updateLineCluster(row, col, 0, 1)
        # update the diagonal neighbors
        self._updateLineCluster(row, col, 1, 1)
        # update the antidiagonal
        self._updateLineCluster(row, col, -1, 1)

    def _updateLineCluster(self, row:int, col:int, rowShift:int, colShift:int)-> None:
        """
        rowshift is if checking the most south or east tile must shift the row down
        colshift is if checking the most south or east tile must shift the col down
        """
        posRow = row + (1*rowShift)
        negRow = row + (-1*rowShift)
        posCol = col + (1*colShift)
        negCol = col + (-1*colShift)
        if 0 <= negRow < self.__startState[0] and 0 <= negCol < self.__startState[1]:
            self.__clusterBoard[negRow][negCol] += 1
        if 0 <= posRow < self.__startState[0] and 0 <= posCol < self.__startState[1]:
            self.__clusterBoard[posRow][posCol] += 1

    def _maxClusterPos(self):
        est = -1
        possibleMoves = self._game.getPossibleMoves()
        for row, col in possibleMoves:
            if est <= self.__clusterBoard[row][col]:
                if est < self.__clusterBoard[row][col]:
                    optimalMoves = []
                    est = self.__clusterBoard[row][col]
                optimalMoves.append((row,col))

        if self.__seed:
            random.seed(self.__seed)
        bestMove = random.choice(optimalMoves)
        self._row, self._col= bestMove[0], bestMove[1]
