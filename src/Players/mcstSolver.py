from game import Game
from Players.player import Player
from Players.friendlyNeighborPlayer import FriendlyNeighborPlayer
import random
import math
import os
import json
import sys
import signal

from collections import defaultdict

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
        self.storeIteration = 500000

        self.path = f"./Players/MCST/mcstStatsV{self.version}.json"
        if not os.path.exists(self.path):
            with open(self.path, "w") as file:
                # check if the file is empty, if so create a new dict
                self.weights = {}
                json.dump(self.weights, file)
        else:
            with open(self.path, "r+") as file: 
                self.weights = json.load(file)

                                                        # num_samples, totScore, (childrenHash, childrenCoords) symHashes (maybe do not need)
        self.weights = defaultdict(lambda: [0, 0, []], self.weights)

        self.should_stop = False
        
        # Register signal handler
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Called when Ctrl+C is pressed"""
        print("\n⚠️  Stop requested. Will finish current iteration and save...")
        self.should_stop = True


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
        print("Training started. Press Ctrl+C to stop gracefully...")
        # run rollouts from the starting state and save the weights every now and then
        while not self._iterations or self.count < self._iterations:
            #o can make this a parameter that is passed in
            # set the game to be the start game
            # self.game = Game(7, 7, 0, 0.5)
            # self.hashes = [0,0,0,0,0,0,0,0]

        
            # Check at SAFE POINT (between iterations)
            if self.should_stop:
                print("Stopping gracefully...")
                self.storeWeights()
                print("✓ Weights saved. Exiting.")
                sys.exit(0)


            self.selection()
            self.count += 1
            assert self.hashes == [0,0,0,0,0,0,0,0] and self.game._moveHistory == [], f"ERROR: not the defualt game upon return, hashes:{self.hashes}, moveHistory: {self.game._moveHistory}, {self.game.getBoard()}, {self.game.getMoveHistory()}"
            if not (self.count+1)%(self.storeIteration+1):
                self.storeWeights()

    def selection(self):
        if len(self.weights[str(self.hashes[0])][2]) == 0:
            score = -self.expansion()
        else:
            #play best ucb move
            # assert self.weights[str(self.hashes[0])][0] > 0, f"log of 0 does not exist in selection, {self.weights[str(self.hashes[0])]}"
            selectedChildIndex = self.UCBSelection()
            selectedMove = self.weights[str(self.hashes[0])][2][selectedChildIndex][1]
            self.updateHash(selectedMove, self.game.getCurrentPlayer())
            self.game.playMove(selectedMove[0], selectedMove[1])
            # redo selection to trverse the tree
            score = -self.selection()
            # undo the best ucb move
            self.game.undo()
            self.updateHash(selectedMove, self.game.getCurrentPlayer())
        
        # back propogation
        self.weights[str(self.hashes[0])][1] += score
        self.weights[str(self.hashes[0])][0] += 1
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
            self.weights[str(parentHash[0])][2].append((self.hashes[0], child))
            assert len(self.weights[str(parentHash[0])][2][-1]) == 2, "children not saved properly"
            
            #testing this is good for wanting to figure out which move is being played but drastically increases the size stored in memory
            # self.weights[str(self.hashes[0])][0] = (child[0], child[1], self.game.getCurrentPlayer())

            # undo the hashes
            self.updateHash(child, self.game.getCurrentPlayer())
            
            # for each symmetry append the child
            #! still need to do check if the sym has been seen already
            # for i in range(len(self.hashes)):
            #     # append the child to the hash
            #     self.weights[self.hashes[i]][2].append(self.hashes[i])

        # assert len(self.weights[str(parentHash[0])][2]) == len(self.weights[str(parentHash[0])][2]), f"ERROR| the length of children hashes {len(self.weights[str(parentHash[0])][3])} does not match then length of children moves {len(self.weights[str(parentHash[0])][4])}"
        # Simulation x2
        # select child to be simulated
        # assert self.weights[str(self.hashes[0])][0] > 0, f"log of 0 does not exist in simulation, {self.weights[str(self.hashes[0])]}"
        selectedChildIndex = self.UCBSelection()
        # play the move to update the game board
        selectedMove = self.weights[str(self.hashes[0])][2][selectedChildIndex][1]
        self.game.playMove(selectedMove[0], selectedMove[1])
        # update its total score and visit count of the selectedChild
        selectedChildHash = str(self.weights[str(self.hashes[0])][2][selectedChildIndex][0])
        self.weights[selectedChildHash][1] += self.randomWalk()
        self.weights[selectedChildHash][1] += self.randomWalk()
        self.weights[selectedChildHash][0] += 2

        # undo the move played
        self.game.undo()
        # return the score
        return self.weights[selectedChildHash][1]

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
        c = 4
        for i, child in enumerate(self.weights[str(self.hashes[0])][2]):
            childHash = child[0]
            if self.weights[str(childHash)][0] == 0:
                # return the index
                return i
            # if a transposition table hit occurs then continue since others should have no visits
            if self.weights[str(self.hashes[0])][0] <= 0 and self.weights[str(childHash)][0] != 0:
                continue
            assert self.weights[str(self.hashes[0])][0] > 0, f"log of 0 does not exist, {self.weights[str(self.hashes[0])]}, child: {self.weights[str(childHash)]}"
            ucb_i = -self.weights[str(childHash)][1]/self.weights[str(childHash)][0]+c*math.sqrt(math.log(self.weights[str(self.hashes[0])][0])/self.weights[str(childHash)][0])
            if ucb_i > max_ucb:
                max_ucb = ucb_i
                max_i = i

        # if all its children have visits from other paths but it itself does not have visits then set its visits to 1 and calculate from that
        if max_ucb == -float('inf'):
            for i, child in enumerate(self.weights[str(self.hashes[0])][2]):
                assert len(child) == 2, f"child: {child}, length not = 2"
                childHash = child[0]
                ucb_i = -self.weights[str(childHash)][1]/self.weights[str(childHash)][0]+c*math.sqrt(math.log(1)/self.weights[str(childHash)][0])
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