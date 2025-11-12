from game import Game
from Players.player import Player
from Players.friendlyNeighborPlayer import FriendlyNeighborPlayer
from Players.mcstSolver import MCSTSolver
import os
import json


from collections import defaultdict

class MCSTPlayer(Player):
    """
    This is the player that implements what is done in MCSTSolver by taking the weights trained and making actions on them
    """
    def __init__(self, name="mcstBot"):
        self.solver = MCSTSolver()
        self.backup = FriendlyNeighborPlayer()
        self._desc = "This player will take the move that is best according to the MCST done prior to playing"
        super().__init__(name)
        self.backupNum = 0
        self.myMove = 0

        assert os.path.exists(self.solver.getPath()), f"file to path {self.solver.getPath()} does not exist"
        with open(self.solver.getPath(), "r+") as file: 
            self.weights = json.load(file)

    def actionMove(self):
        assert self._game, "no game: set the game"
        assert self._game.getCurrentPlayer() == self._playerOrder, f"ERROR: not player {self._playerOrder}'s turn, but tries to play for {self._game.getCurrentPlayer()}"

        # get the hash of the board
        bestI = 0
        mostVisits = 0
        curBoardHash = self.boardToHash()
        # when the board has never been seen in testing act as backup plan
        if str(curBoardHash) not in self.weights:
            self.backupNum += 1
            print("backupMove", self.backupNum)
            self.backup.setGame(self._game, self.getPlayerOrder())
            row, col = self.backup.actionMove()
            return row, col
        for i, child in enumerate(self.weights[str(curBoardHash)][2]):
            childHash = child[0]
            # if the child has never been visited ignore the child
            if str(childHash) not in self.weights:
                continue
            if self.weights[str(childHash)][0] > mostVisits:
                bestI = i
                mostVisits = self.weights[str(childHash)][0]
        
        self.myMove += 1
        print("MCSTMove", self.myMove)
        # how can I have a child that is in the childHashes but not in the ChildMoves
        bestMove = self.weights[str(curBoardHash)][2][bestI][1]
        self._game.playMove(bestMove[0], bestMove[1])
        return bestMove

    def boardToHash(self):
        initBoard = self._game.getInit()
        boardHash = 0
        for row in range(initBoard[0]):
            for col in range(initBoard[1]):
                if self._game._board[row][col] == 0:
                    continue
                elif self._game._board[row][col] == 1:
                    shift = 0
                elif self._game._board[row][col] == 2:
                    shift = 49

                index = row*initBoard[0] + col
                boardHash = boardHash ^ (1 << shift+index)
        
        return boardHash
