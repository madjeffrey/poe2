from Players.mcstPlayer import MCSTSolver
from game import Game

if __name__ == "__main__":
    mcst = MCSTSolver(Game(7,7,0,0.5))
    mcst.runMCST()