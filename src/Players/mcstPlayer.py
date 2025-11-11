from game import Game
from Players.player import Player
from Players.friendlyNeighborPlayer import FriendlyNeighborPlayer
import random
import math
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
        if str(curBoardHash) not in self.weights.keys():
            self.backup.setGame(self._game, self.getPlayerOrder())
            row, col = self.backup.actionMove()
            return row, col
        for i, childHash in enumerate(self.weights[str(curBoardHash)][3]):
            # if the child has never been visited ignore the child
            if str(childHash) not in self.weights.keys():
                continue
            if self.weights[str(childHash)][1] > mostVisits:
                bestI = i
                mostVisits = self.weights[str(childHash)][1]
        
        # how can I have a child that is in the childHashes but not in the ChildMoves
        bestMove = self.weights[str(curBoardHash)][4][bestI]
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

class MCSTSolver():
    """
    assume the board is a 7x7 with no cutoff and 0.5 advantage
    this class is used to train to be able to find the weights of each state, it allows for the MCST player to have good staring weights for each simulation
    todo:
    [x] save the weights
    [ ] make sure that the score difference is what is should be
    Question:
        - do I care how much I beat my opponnent by or just that I beat my opponent
    """
    def __init__(self, game:Game=None):
        self.game = game
                        # id, hor, ver, dia, anti, 90, 180, 270
        self.hashes = [0,0,0,0,0,0,0,0]
        self.version = "1"
        self.save = True
        self._iterations = None
        self.storeIteration = 10000

        self.path = f"./Players/MCST/mcstStatsV{self.version}.json"
        if not os.path.exists(self.path):
            with open(self.path, "w") as file:
                # check if the file is empty, if so create a new dict
                self.weights = {}
                json.dump(self.weights, file)
        else:
            with open(self.path, "r+") as file: 
                self.weights = json.load(file)

                                                        # move, num_samples, totScore, childrenHash, childrenCoords, symHashes (maybe do not need)
        self.weights = defaultdict(lambda: [-1, 0, 0, [], []], self.weights)


    def setSave(self, save:bool):
        self.save = save

    def setGame(self, game):
        self.game = game

    def setIterations(self, iterations, storeIterations=10000):
        self._iterations = iterations
        self.storeIteration = storeIterations
    
    def getPath(self):
        return self.path

    def runMCST(self):
        self.count = 0
        # run rollouts from the starting state and save the weights every now and then
        while not self._iterations or self.count < self._iterations:
            #o can make this a parameter that is passed in
            # set the game to be the start game
            # self.game = Game(7, 7, 0, 0.5)
            # self.hashes = [0,0,0,0,0,0,0,0]
            self.selection()
            self.count += 1
            assert self.hashes == [0,0,0,0,0,0,0,0] and self.game._moveHistory == [], f"ERROR: not the defualt game upon return, hashes:{self.hashes}, moveHistory: {self.game._moveHistory}, {self.game.getBoard()}, {self.game.getMoveHistory()}"
            if not (self.count+1)%(self.storeIteration+1):
                self.storeWeights()

    def selection(self):
        if len(self.weights[str(self.hashes[0])][3]) == 0:
            score = -self.expansion()
        else:
            #play best ucb move
            # assert self.weights[str(self.hashes[0])][0] > 0, f"log of 0 does not exist in selection, {self.weights[str(self.hashes[0])]}"
            selectedChildIndex = self.UCBSelection()
            selectedMove = self.weights[str(self.hashes[0])][4][selectedChildIndex]
            self.updateHash(selectedMove, self.game.getCurrentPlayer())
            self.game.playMove(selectedMove[0], selectedMove[1])
            # redo selection to trverse the tree
            score = -self.selection()
            # undo the best ucb move
            self.game.undo()
            self.updateHash(selectedMove, self.game.getCurrentPlayer())
        
        # back propogation
        self.weights[str(self.hashes[0])][2] += score
        self.weights[str(self.hashes[0])][1] += 1
        return score

    def expansion(self):
        ## change gears to only do this without symmetry to be added after
        # if the state to expand is terminal, then return the diff value of the ending scores
        if self.game.gameOver():
            # get the curret score difference relative to the player to play at the node to be expanded
            ## runs 2 so that is why the difference is never 0.5
            p1S, p2S = self.game.getPlayerScores()
            score = p1S - p2S
            if self.game.getCurrentPlayer() == 2:
                score = -score
            return -score
        
        children = self.game.getPossibleMoves()
        parentHash = self.hashes.copy()
        for child in children:
            # update the hashes as if this move was played
            self.updateHash(child, self.game.getCurrentPlayer())
            
            # add child to list of children through its hash
            self.weights[str(parentHash[0])][3].append(self.hashes[0])
            self.weights[str(parentHash[0])][4].append(child)
            
            #testing this is good for wanting to figure out which move is being played but drastically increases the size stored in memory
            # self.weights[str(self.hashes[0])][0] = (child[0], child[1], self.game.getCurrentPlayer())

            # undo the hashes
            self.updateHash(child, self.game.getCurrentPlayer())
            
            # for each symmetry append the child
            #! still need to do check if the sym has been seen already
            # for i in range(len(self.hashes)):
            #     # append the child to the hash
            #     self.weights[self.hashes[i]][2].append(self.hashes[i])

        assert len(self.weights[str(parentHash[0])][4]) == len(self.weights[str(parentHash[0])][3]), f"ERROR| the length of children hashes {len(self.weights[str(parentHash[0])][3])} does not match then length of children moves {len(self.weights[str(parentHash[0])][4])}"
        # Simulation x2
        # select child to be simulated
        # assert self.weights[str(self.hashes[0])][0] > 0, f"log of 0 does not exist in simulation, {self.weights[str(self.hashes[0])]}"
        selectedChildIndex = self.UCBSelection()
        # play the move to update the game board
        selectedMove = self.weights[str(self.hashes[0])][4][selectedChildIndex]
        self.game.playMove(selectedMove[0], selectedMove[1])
        # update its total score and visit count of the selectedChild
        selectedChildHash = str(self.weights[str(self.hashes[0])][3][selectedChildIndex])
        self.weights[selectedChildHash][2] += self.randomWalk()
        self.weights[selectedChildHash][2] += self.randomWalk()
        self.weights[selectedChildHash][1] += 2

        # undo the move played
        self.game.undo()
        return self.weights[selectedChildHash][2]

    def randomWalk(self):
        # if terminal game return the difference in scores
        if self.game.gameOver():
            p1S, p2S = self.game.getPlayerScores()
            score = p1S - p2S
            if self.game.getCurrentPlayer() == 2:
                score = -score
            return score

        # chose a random legal move
        moves = self.game.getPossibleMoves()
        randomMove = moves[random.randint(0, len(moves)-1)]
        # play the move
        self.game.playMove(randomMove[0], randomMove[1])
        # make next random move
        score = -self.randomWalk()
        self.game.undo()
        return score

    def UCBSelection(self):
        max_ucb = -float('inf')
        max_i = 0
        c = 1
        for i, childHash in enumerate(self.weights[str(self.hashes[0])][3]):
            if self.weights[str(childHash)][1] == 0:
                # return the index
                return i
            # if a transposition table hit occurs then continue since others should have no visits
            if self.weights[str(self.hashes[0])][1] <= 0 and self.weights[str(childHash)][1] != 0:
                continue
            assert self.weights[str(self.hashes[0])][1] > 0, f"log of 0 does not exist, {self.weights[str(self.hashes[0])]}, child: {self.weights[str(childHash)]}"
            ucb_i = -self.weights[str(childHash)][2]/self.weights[str(childHash)][1]+c*math.sqrt(math.log(self.weights[str(self.hashes[0])][1])/self.weights[str(childHash)][1])
            if ucb_i > max_ucb:
                max_ucb = ucb_i
                max_i = i

        # if all its children have visits from other paths but it itself does not have visits then set its visits to 1
        if max_ucb == -float('inf'):
            for i, childHash in enumerate(self.weights[str(self.hashes[0])][3]):
                ucb_i = -self.weights[str(childHash)][2]/self.weights[str(childHash)][1]+c*math.sqrt(math.log(1)/self.weights[str(childHash)][1])
                if ucb_i > max_ucb:
                    max_ucb = ucb_i
                    max_i = i
        # return the index of the max
        return max_i

    def updateHash(self, move, player):
        """
        when this function is called it should update all the hashes to have the hash of the move played
        """
        # set the shift for if it is player 2
        shift = 0
        if player == 2:
            shift = 49
        
        assert 0 <= move[0] < 7 and 0 <= move[1] < 7, "move is not legal"
        # hashes should look like 0-48 bits = left to right top to bottom for player 1, 49-97 same for player 2
        # do i want my current hash and then next hashes to store as parrents I mean it is the same to do and undo as to return
        #i could add asserts to make sure no square has two moves played in it but this should never happen if done carefully
        # update the identity hash
        index = move[0]*7 + move[1]
        self.hashes[0] = self.hashes[0] ^ 1 << shift+index
        # update the horizontal hash
        index = (6-move[0])*7 + move[1]
        self.hashes[1] = self.hashes[1] ^ 1 << shift+index
        # update the vertical hash
        index = move[0]*7 + (6-move[1])
        self.hashes[2] = self.hashes[2] ^ 1 << shift+index
        # update the 180 hash
        index = (6-move[0])*7 + (6-move[1])
        self.hashes[3] = self.hashes[3] ^ 1 << shift+index
        # update the diagonal hash
        index = move[1]*7 + move[0]
        self.hashes[4] = self.hashes[4] ^ 1 << shift+index
        # update the antidiagonal hash
        index = (6-move[1])*7 + (6-move[0])
        self.hashes[5] = self.hashes[5] ^ 1 << shift+index
        # update the 90 hash
        index = move[1]*7 + (6-move[0])
        self.hashes[7] = self.hashes[7] ^ 1 << shift+index
        # update the 270 hash
        index = (6-move[1])*7 + move[0]
        self.hashes[6] = self.hashes[6] ^ 1 << shift+index
        return 
        

    def storeWeights(self):
        with open(self.path, "r+") as file:
            file.seek(0)
            json.dump(self.weights, file)
            file.truncate()

    def updateWeights(self):
        pass



if __name__ == "__main__":
    mcst = MCSTSolver()
    mcst.runMCST()