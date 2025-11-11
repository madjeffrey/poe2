from simulation import Simulation
from Players.randomPlayer import RandomPlayer
from Players.clusterPlayer import ClusterPlayer
from Players.friendlyNeighborPlayer import FriendlyNeighborPlayer 
from test import TestRun


"""
todo:
    - test for if the game holds even with undo every random amount of chances
"""

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




    # sim = Simulation((rows, cols, cutoff, handicap), friendlyPlayer, randPlayer, 5000, (False, True, True, False, 0, 1000))
    # sim.run()
    test = TestRun((rows, cols, cutoff, handicap), friendlyPlayer, cluPlayer, 5000, (False, True, True, False, 0, 1000))
    test.run()



