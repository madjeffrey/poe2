from player import Player
from game import Game
import random
import math
import os
import json

from collections import defaultdict

class MCSTPlayer(Player):
    """
    todo:
    [] save the weights
    Question:
    - do I care how much I beat my opponnent by or just that I beat my opponent
    """
    pass

class MCSTSolver(Player):
    """
    assume the board is a 7x7 with no cutoff and 0.5 advantage
    this class is used to train to be able to find the weights of each state, it allows for the MCST player to have good staring weights for each simulation
    todo:
    [] save the weights
    Question:
        - do I care how much I beat my opponnent by or just that I beat my opponent
    """
    def __init__(self, game:Game):
        self.game = game
                        # id, hor, ver, dia, anti, 90, 180, 270
        self.hashes = [0,0,0,0,0,0,0,0]
        self.version = "1"
        path = f"./Players/MCST/mcstStatsV{self.version}.json"
        if not os.path.exists(path):
            with open(path, "w") as file:
                # check if the file is empty, if so create a new dict
                self.weights = {}
                json.dump(self.weights, file)
        else:
            with open(self._classPath, "r+") as file:
                self.weights = json.load(file)

                                                        # num samples, totScore, childrenHash, symHashes (maybe do not need)
        self.weights = defaultdict(self.weights, lambda: [0, 0, [], []])

    def runMCST(self):
        self.selection()

    def setGame(self, game):
        self.game = game

    def updateHash(self, move, player):
        """
        when this function is called it should update all the hashes to have the hash of the move played
        """
        # set the shift for if it is player 2
        shift = 1
        if player == 2:
            shift = 49
        
        assert 0<= move[0] < 7 and 0 <= move[1] < 7, "move is not legal"
        # hashes should look like 0-48 bits = left to right top to bottom for player 1, 49-97 same for player 2
        # do i want my current hash and then next hashes to store as parrents I mean it is the same to do and undo as to return
        #i could add asserts to make sure no square has two moves played in it but this should never happen if done carefully
        nextHash = []
        # update the identity hash
        index = move[0]*7 + move[1]
        nextHash[0] = self.hashes[0] | 1 << shift+index
        # update the horizontal hash
        index = (6-move[0])*7 + move[1]
        nextHash[1] = self.hashes[1] | 1 << shift+index
        # update the vertical hash
        index = move[0]*7 + (6-move[1])
        nextHash[2] = self.hashes[2] | 1 << shift+index
        # update the 180 hash
        index = (6-move[0])*7 + (6-move[1])
        nextHash[3] = self.hashes[3] | 1 << shift+index
        # update the diagonal hash
        index = move[1]*7 + move[0]
        nextHash[4] = self.hashes[4] | 1 << shift+index
        # update the antidiagonal hash
        index = (6-move[1])*7 + (6-move[0])
        nextHash[5] = self.hashes[5] | 1 << shift+index
        # update the 90 hash
        index = (6-move[1])*7 + move[0]
        nextHash[6] = self.hashes[6] | 1 << shift+index
        # update the 270 hash
        index = move[1]*7 + (6-move[0])
        nextHash[7] = self.hashes[7] | 1 << shift+index
        return nextHash
        

    def saveValue(self):
        pass

    def selection(self):
        if len(self.weights[2]) == 0:
            score = -self.expansion()
    
    def expansion(self):
        # get the curret score difference relative to the player to play at the node to be expanded
        ## change gears to only do this without symmetry to be added after
        p1S, p2S = self.game.getPlayerScores()
        score = p1S - p2S
        if self.game.getCurrentPlayer() == 2:
            score = -score

        # if the state to expand is terminal, than return the value of the ending scores
        if self.game.gameOver():
            return -score
        
        children = self.game.getPossibleMoves()
        for child in children:
            # update the hashes as if this move was played
            nextHash = self.updateHash(child, 1 if self.game.getCurrentPlayer() == 2 else 2)
            
            # add child to list of children through its hash
            self.weights[self.hashes[0]][2].append(nextHash[0])
            
            # for each symmetry append the child
            #! still need to do check if the sym has been seen already
            # for i in range(len(nextHash)):
            #     # append the child to the hash
            #     self.weights[self.hashes[i]][2].append(nextHash[i])

        # Simulation
        selectedChild = self.UCBSelection()



    def UCBSelection(self):
        max_ucb = -float('inf')
        max_i = 0
        c = 1
        for i, childHash in enumerate(self.weights[self.hashes[0]][2]):
            if self.weights[childHash][0] == 0:
                return childHash
            ucb_i = -self.weights[childHash][1]/self.weights[childHash][0]+c*math.sqrt(math.log(self.weights[self.hashes[0]][0])/self.weights[childHash][0])
            if ucb_i > max_ucb:
                max_ucb = ucb_i
                max_i = i
        return self.weights[self.hashes[0]][2][max_i]


class MCTS_node:
    def __init__(self, state):
        self.visits = 0
        self.score_total = 0
        self.children = []
        self.state = state.get_copy()

def random_walk(state): # returns the relative score
    score = state.get_relative_score()
    if score is not None:
        return score
    moves = state.get_moves()
    rand_move = moves[random.randint(0,len(moves)-1)]
    state.make_move(rand_move)
    score = -random_walk(state)
    state.undo_move(rand_move)
    return score

def UCB_selection(node, c=1):
    max_ucb = -float('inf')
    max_i = 0
    for i, child in enumerate(node.children):
        if child.visits == 0:
            return node.children[i]
        ucb_i = -child.score_total/child.visits+\
            c*math.sqrt(math.log(node.visits)/child.visits)
        if ucb_i > max_ucb:
            max_ucb = ucb_i
            max_i = i
    return node.children[max_i]

def expansion(node):
    score = node.state.get_relative_score()
    if score is not None: #terminal node
        return -score
    moves = node.state.get_moves()
    for move in moves:
        node.state.make_move(move)
        node.children.append(MCTS_node(node.state))
        node.state.undo_move(move)
    # Simulation:
    child = UCB_selection(node)
    child.score_total += random_walk(child.state)
    child.visits = 1
    return child.score_total

def selection(node):
    if len(node.children) == 0:
        score = -expansion(node)
    else:
        score = -selection(UCB_selection(node))
    # Backpropagation
    node.score_total += score
    node.visits += 1
    return score

def MCTS_policy(state, time_budget=0.1):
    t0 = time.time()
    root_node = MCTS_node(state)
    while time.time()-t0 < time_budget-0.01:
        selection(root_node)
    best_i = 0
    most_visits = 0
    for i, child in enumerate(root_node.children):
        if child.visits > most_visits:
            best_i = i
            most_visits = child.visits
    return state.get_moves()[best_i]