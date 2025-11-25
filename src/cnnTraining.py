import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import math


device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
print(f"Using {device} device")
# parameters

"""
Version 1:
    take board
    make board a 2 dimension tile encoding 1 for the current player pieces, one for the opposing player pieces
        - is it good to have 0 for empty 1 for current player and -1 for opposite player, this would then give me the value score of the current player. How good is the position for the current player
        - what would this learn? I would think it would learn how good is the state for the given player
        - the first would learn what is a good combination of my moves
        - the second would learn what is a good combination of their moves
        - issue: there would always have half of their board empty. 
        Goal: given a state give me the move that is best for me to play. 
    Run this through many simulations using monte carlo methods to update the weights of the neural network
    49x2 -> 64 -> 32 -> 16 -> 1
"""

# Version 1

class NN1(nn.Module):
    def __init__(self):
        super().__init__()
        self.NNStack = nn.Sequential(
            nn.Linear(98, 64),
            nn.ReLU(),
            nn.Linear(64,32),
            nn.ReLU(),
            nn.Linear(32,16),
            nn.ReLU(),
            nn.Linear(16,1)
        )
    
    def forward(self, board, action, curPlayer):
        """
        Return the expected Q(S,A) given a state(board) and action
        args:
            board = board position
            curPlayer = 1 or 2 which player is to play
        """
        tensor = self.processBoard(board, curPlayer)
        return
    
    def processBoard(self, board, curPlayer):
        """
        function to turn a board into a valid feature vector

        args:
            7x7 board in this case
            board = nxm lists of int (0,1,2)
            curPlayer = the current player to move 1 or 2
        
        returns:
            a 1x2nm array where the first nm coordinates are active if the current player has played a square on that cell
        """

        """
        I could model this with the action by a 0-48 added on top of this that would indicate the action to take, how else could I even model this, I could have the state vector for each action, but maybe a want the weights for each action
        """
        numRow = len(board)
        numCol = len(board[0])
        assert numRow == 7 and numCol == 7, f"ERROR: {numRow}x{numCol} matrix not 7x7 matrix for poe2 ass 4"
        tensor = np.zeros(2*numRow*numCol, dtype=float)
        for row in range(numRow):
            for col in range(numCol):
                assert board[row][col] in [0,1,2], f"ERROR: invalid board state at ({row}, {col}), {board[row][col]}"
                if board[row][col] == 0:
                    return
                elif board[row][col] == curPlayer:
                    tensor[2*(row*len(board[0]) + col)] = 1
                else:
                    tensor[2*(row*len(board[0]) + col) + 1] = 1


        return tensor



class Test(NN1):
    def runTest(self):
        print("Starting Test ...")
        self.testProcessBoard()

        print("All Tests Passed")


    def testProcessBoard(self):
        board = [[1,1,1,1,1,1,1], [1,1,1,1,1,1,1], [1,1,1,1,1,1,1], [1,1,1,2,2,2,2], [2,2,2,2,2,2,2], [2,2,2,2,2,2,2], [2,2,2,2,2,2,2]]
        
        expT = []
        for _ in range(24):
            expT += [1] + [0]
        for _ in range(25):
            expT += [0] + [1]

        assert np.array_equal(np.array(expT), self.processBoard(board, 1)), f"TEST FAIL| {expT}, {self.processBoard(board, 1)}"

if __name__ == "__main__":
    t = Test()
    t.runTest()
