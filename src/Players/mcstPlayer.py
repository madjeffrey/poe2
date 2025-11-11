from player import Player
from game import Game
import random
import math

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
    this class is used to train to be able to find the weights of each state, it allows for the MCST player to have good staring weights for each simulation
    todo:
    [] save the weights
    Question:
    - do I care how much I beat my opponnent by or just that I beat my opponent
    """
    def __init__(self, game:Game):
        self.game = game

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