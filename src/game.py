from datetime import datetime


"""
Question:
- who should save the stats for the game, if I want to have a simulation class that can play many of different 2 player alternating games then game should save it, I think this is how I want it


todo:
[x] make w+ into r+ by checking first if the file exists or not
[x] edit id so that it is only : separated numbers
[x] make it so that the players wins and losses are divided by who he beat as well, record against opponent (should be a dict to key in opponent)
[] get current working directory to calculate path to store the statistics as for now must be run in src

tasks:
[] test my game to find the bug with my score calculation
[] update calc score so that it is more efficient using my algorithm


maybe:
[] make it so that the description of the player is shown in the game logs and player logs
[] update so that the wins are calculated for the given board startState, size, cutoff, handicap
"""

class Game:
    """
    The game class is a representation of the environment in which _players are able to interact with.
    This includes holding game state as well as provides functionality to make actions

    Actions:
        play: plays a move
        getPlayerScore: gets the current score of the game state
        isLegal: checks if a given move is legal
        winner: says if the board is over and someone has won, 0 = nobody, 1 = _player 1, 2 = _player 2
        undo: allows to roll back the game state
    """    
    ## does python always pass by reference?
    def __init__(self, numRows:int, numCols:int, scoreCutoff:float, handicap:float):
        # generate id based on time of initializaiton
        # Current time
        now = datetime.now()
        # Format: YYYY-MM-DD HH:MM:SS.mmm
        self._id = now.strftime("%Y_%m_%d_%H_%M_%S_") + f"{int(now.microsecond/1000):08d}" 
        # Game state  
        # all caps = const
        self._NUMCOLS = int(numCols)
        self._NUMROWS = int(numRows)
        self._SCORECUTOFF = float(scoreCutoff)
        self._NUMTILES = self._NUMCOLS * self._NUMROWS
        self._HANDICAP = float(handicap)
        self._won = 0
        self._numMoves = 0
        self._moveHistory = [] #((row:int,col:int),(_p1Score:float, _p2Score:float), cur_player:int, winner:int)
        self._currentPlayer = 1 # 1 _player 1 or 2 _player 2
        self._p1Score = int(0)
        self._p2Score = float(handicap)
        self._newGame = True ## could change this whole check to just be if the board is empty, but this would be called often, and so it would be slow to compute

        # needed for my efficient implementation of _lineCheck
        # self.matrixLines = [[[0 for _ in range(4)] for _ in range(self._NUMCOLS)] for _ in range(self._NUMROWS)] #[/, \, |, -]

        self._board = [[0]*self._NUMCOLS for _ in range(self._NUMROWS)]


    def __str__(self):
        '''
        show the board
        '''
        output = str()
        for row in self._board:
            output += " ".join(["_" if v == 0 else str(v) for v in row]) + "\n"
        output += f"\nPlayer 1 has score: {self._p1Score} \nPlayer 2 has score: {self._p2Score}"
        if self._won != 0:
            output += "\n" + f"***game over: winner is {self._won}***"
        
        return output + "\n____________________________________\n"


    # getter and setter functions
    def getId(self) -> str:
        """
        returns:
            the id for a given game
        """
        return self._id

    # getters since we do not want any setters as the board should only be manipulated through the play function
    def getBoard(self) -> list:
        """
        Args:
            None
        Returns: 
            list: of lists that are the board state
        """
        return self._board
        ## does this return a reference or the actual board

    def getWinner(self) -> int:
        """
        Args:
            None
        Returns:
            int: 1 -> player 1 won | 2 -> player 2 won | 0 -> no winner yet
        """
        self.gameOver()
        return self._won
    
    def getInit(self)->tuple:
        """
        Args:
            None
        Returns:
            tuple:(numRows, numCols, scoreCutoff, Handicap)
        """
        return (self._NUMROWS, self._NUMCOLS, self._SCORECUTOFF, self._HANDICAP)
    
    def getMoveHistory(self) -> tuple:
        """
        Args:
            None
        Returns:
        tuple:  index 0 | list: move history ((row:int,col:int),(_p1Score:float, _p2Score:float), cur_player:int, winner:int) | int: index 1: | int: len of move history
        """
        return (self._moveHistory, self._numMoves)
    
    def getPlayerScores(self) -> tuple:
        """
        Args:
            None
        Returns: 
            tuple: (player1Score, Player2Score)
        """

        return (self._p1Score, self._p2Score)

    def getCurrentPlayer(self):
        """
        returns who the current player is
        Args:
            None
        Returns: 
            int: the current player | 1 = player 1 | 2 = player 2
        """
        return self._currentPlayer

    def getPossibleMoves(self) -> list:
        """
        Args:
            None
        Returns: 
            list: all spaces that have no stones
        """
        moves = []
        for y in range(self._NUMROWS):
            for x in range(self._NUMCOLS):
                if self._board[y][x] == 0:
                    moves.append((y, x))
        return moves

    def getIgnoreMirrorMatch(self):
        return self._ignoreMirrorMatch
    
    def setIgnoreMirrorMatch(self, ignoreMirrorMatch):
        self._ignoreMirrorMatch = ignoreMirrorMatch
    
    def getRecordGames(self):
        return self._recordGames
    
    def setRecordGames(self, recordGames):
        self._recordGames = recordGames

    def getRecordStats(self):
        return self._recordStatistics
    
    def setRecordStats(self, recordStats):
        self._recordStatistics = recordStats
    
    def getIsNewGame(self):
        return self._newGame
    
    
    def playMove(self, row, col) -> int:
        '''
        >> play <col> <row>
        Places the current _player's piece at position (<col>, <row>). Check if the move is legal before playing it.
        can return false if the move is illegal

        Args:
            int: row
            int: column

        Returns:
            int: -1 if illegal move | 1 if move successful | 2 if there is a winner

        '''
        if not self.isLegal(row, col):
            return -1
        if self._won != 0:
            return 2

        ## could these be assertions, or then this would stop the program which is not what I want
        # It is not a newGame since a move has been played
        self._newGame = False
        # update the board state
        
        # calculate the score through all the four possible directions of lines
        self._calcScore(row, col)

        # keep track of the number of moves played
        self._numMoves += 1 

        self.gameOver()

        # add the move history to the list for undo
        self._moveHistory.append(((row,col),(self._p1Score, self._p2Score), self._currentPlayer , self._won))

        # update the board needs to happen after calcScore because it needs to check for neighbors that are not the new move
        self._board[row][col] = self._currentPlayer
        if self._currentPlayer == 2:
            self._currentPlayer = 1
        else:
            self._currentPlayer = 2
    

        return 1


    def isLegal(self, row:int, col:int)->bool:
        """
        Args:
            int: row
            int: column

        Returns:
            True if move is legal
            False if move is illegal
        """
        if self._won == 0 and self._board[row][col] == 0:
            return True
        
        return False

    def undo(self):
        '''
        Undoes the last move.

        Returns:
            True if undo was successful 

            False if no moves to undo
        '''
        if not self._moveHistory:
            self._newGame = True
            return False
        
        status = self._moveHistory.pop()
        self._numMoves -= 1
        self._board[status[0][0]][status[0][1]] = 0
        if self._moveHistory:
            newState = self._moveHistory[-1]
            self._p1Score = newState[1][0]
            self._p2Score = newState[1][1]
            self._currentPlayer = newState[2]
            self._won = newState[3]
        else:
            self._numMoves = 0
            self._p1Score = 0
            self._p2Score = self.HANDICAP
            self._currentPlayer = 1
            self._won = 0
        return True

    def gameOver(self)-> bool:
        """
        Updates the winner if there is one

        Returns:
            True if the game is over

            False if the game is not over
        """

        
        if self._SCORECUTOFF == 0 and self._numMoves != self._NUMTILES:
            self._won = 0
            return False

        elif self._SCORECUTOFF != 0 and self._p1Score >= self._SCORECUTOFF:
            self._won = 1
            return True
        
        elif self._SCORECUTOFF != 0 and self._p2Score >= self._SCORECUTOFF:
            self._won = 2
            return True
        
        elif self._numMoves == self._NUMTILES:
            if self._p1Score > self._p2Score:
                self._won = 1
            else:
                self._won = 2 
            return True
        
        else:
            self._won = 0
        assert self._numMoves <= self._NUMTILES, "number of tiles exceed possible"
        return False


    def _calcScore(self, row:int, col:int)->int:
        """
        adds the score for all types of lines that can be made Linearly
        """
        # assert proper row and col is given
        assert 0 <= row < self._NUMROWS, "row is out of bounds"
        assert 0 <= col < self._NUMCOLS, "col is out of bounds"

        flag = 0
        # check vertical neighbors
        if self._lineCheck(row, col, 1, 0):
            flag = 1
        # check horizontal neighbors
        if self._lineCheck(row, col, 0, 1):
            flag = 1
        # check the diagonal neighbors
        if self._lineCheck(row, col, 1, 1):
            flag = 1
        # check the antidiagonal
        if self._lineCheck(row, col, -1, 1):
            flag = 1
        if flag == 0:
            if self._currentPlayer == 1:
                self._p1Score += 1
            else:
                self._p2Score += 1

        return 

    def _lineCheck(self, row:int, col:int, rowShift:int, colShift:int)-> int:
        """
        rowshift is if checking the most south or east tile must shift the row down

        colshift is if checking the most south or east tile must shift the col down

        used to add the scores for a row and column of a given line type (dia, antidia, vertical, horizontal)
        
        Formula: + new line length points - old points contributed by num above - old points contributed by num below
        """
        a = (1*rowShift)
        b = (-1*rowShift)
        c = (1*colShift)
        d = (-1*colShift)


        posRow = row + a
        negRow = row + b
        posCol = col + c
        negCol = col + d

        numAbove = 0
        numBelow = 0

        while 0 <= negRow < self._NUMROWS and 0 <= negCol < self._NUMCOLS and self._board[negRow][negCol] == self._currentPlayer:
            numBelow += 1
            negRow += b
            negCol += d
        while 0 <= posRow < self._NUMROWS and 0 <= posCol < self._NUMCOLS and self._board[posRow][posCol] == self._currentPlayer:
            numAbove += 1
            posRow += a
            posCol += c

        if numAbove == 0 and numBelow == 0:
            return False
        
        # update the score
        if self._currentPlayer == 1:
            self._p1Score += 2**(numAbove + numBelow)
        else:
            self._p2Score += 2**(numAbove + numBelow)

        # need to find the supersets to remove
        # if above does not have a neighbor, subtract 1 because it added 1 before
        #* if above has a neighbor and the num above == 1 then don't subtract any becaus it's line of that type did not exist / this is the main thing that I was missing for it to work
        # else subtract numAbove-1
        ## I feel I am missing something for double connctions but maybe not because I add the whole line then get rid of the rest
        posRow = row + a
        negRow = row + b
        posCol = col + c
        negCol = col + d

        if numAbove != 0:
            # this should already hold and may be redundant
            assert 0 <= posRow < self._NUMROWS and 0 <= posCol < self._NUMCOLS, "checking for an above cell that is out of bounds"
            neigh = self.__checkIfNeighbor(posRow, posCol)
            if self._currentPlayer == 1:
                if not neigh:
                    self._p1Score -= 1
                elif numAbove != 1:
                    self._p1Score -= 2**(numAbove-1)
            else:
                if not neigh:
                    self._p2Score -= 1
                elif numAbove != 1:
                    self._p2Score -= 2**(numAbove-1)

        if numBelow != 0:
            # this should already hold and may be redundant
            assert 0 <= negRow < self._NUMROWS and 0 <= negCol < self._NUMCOLS, "checking for a below cell that is out of bounds"
            neigh = self.__checkIfNeighbor(negRow, negCol)
            if self._currentPlayer == 1:
                if not neigh:
                    self._p1Score -= 1
                elif numBelow != 1:
                    self._p1Score -= 2**(numBelow-1)
            else:
                if not neigh:
                    self._p2Score -= 1
                elif numBelow != 1:
                    self._p2Score -= 2**(numBelow-1)

        return True
    

    def __checkIfNeighbor(self, row:int, col:int)->int:
        """
        used to check if a given tile has any neighbors
        """
        # assert proper row and col is given
        assert 0 <= row < self._NUMROWS, "row is out of bounds, neigh"
        assert 0 <= col < self._NUMCOLS, "col is out of bounds, neigh"

        # check antidia, diagonal, horizontal, vertical
        return self.__checkSuperset(row, col, -1, 1) or self.__checkSuperset(row, col, 1, 1) or self.__checkSuperset(row, col, 0, 1) or self.__checkSuperset(row, col, 1, 0)

    def __checkSuperset(self, row:int, col:int, rowShift:int, colShift:int)-> int:
        """
        rowshift is if checking the most south or east tile must shift the row down
        colshift is if checking the most south or east tile must shift the col down
        
        returns:
            True if there is a neighbor that is of the same type
            False if no neighbor
        """
        posRow = row + (1*rowShift)
        negRow = row + (-1*rowShift)
        posCol = col + (1*colShift)
        negCol = col + (-1*colShift)

        if 0 <= negRow < self._NUMROWS and 0 <= negCol < self._NUMCOLS:
            if self._board[negRow][negCol] == self._currentPlayer:
                return True

        if 0 <= posRow < self._NUMROWS and 0 <= posCol < self._NUMCOLS:
            ##s can update it so that there is priority for each players move or only your moves count
            if self._board[posRow][posCol] == self._currentPlayer:
                return True

        return False


    # want to eventually switch to my score calculation
    def calcScoreSlow(self):
        """
        This function calculates the score from scratch given the current state by iterating over all lines for every direction

        Args:
            None

        Returns:
            tuple: (Player 1 Score: int, Player 2 Score: int)
        """
        _p1Score = 0
        _p2Score = self._HANDICAP

        # Progress from left-to-right, top-to-bottom
        # We define lines to start at the topmost (and for horizontal lines leftmost) point of that line
        # At each point, score the lines which start at that point
        # By only scoring the starting points of lines, we never score line subsets
        for y in range(self._NUMROWS):
            for x in range(self._NUMCOLS):
                c = self._board[y][x]
                if c != 0:
                    lone_piece = True # Keep track of the special case of a lone piece
                    # Horizontal
                    hl = 1
                    if x == 0 or self._board[y][x-1] != c: #Check if this is the start of a horizontal line
                        x1 = x+1
                        while x1 < self._NUMCOLS and self._board[y][x1] == c: #Count to the end
                            hl += 1
                            x1 += 1
                    else:
                        lone_piece = False
                    # Vertical
                    vl = 1
                    if y == 0 or self._board[y-1][x] != c: #Check if this is the start of a vertical line
                        y1 = y+1
                        while y1 < self._NUMROWS and self._board[y1][x] == c: #Count to the end
                            vl += 1
                            y1 += 1
                    else:
                        lone_piece = False
                    # Diagonal
                    dl = 1
                    if y == 0 or x == 0 or self._board[y-1][x-1] != c: #Check if this is the start of a diagonal line
                        x1 = x+1
                        y1 = y+1
                        while x1 < self._NUMCOLS and y1 < self._NUMROWS and self._board[y1][x1] == c: #Count to the end
                            dl += 1
                            x1 += 1
                            y1 += 1
                    else:
                        lone_piece = False
                    # Anit-diagonal
                    al = 1
                    if y == 0 or x == self._NUMCOLS-1 or self._board[y-1][x+1] != c: #Check if this is the start of an anti-diagonal line
                        x1 = x-1
                        y1 = y+1
                        while x1 >= 0 and y1 < self._NUMROWS and self._board[y1][x1] == c: #Count to the end
                            al += 1
                            x1 -= 1
                            y1 += 1
                    else:
                        lone_piece = False
                    # Add scores for found lines
                    for line_length in [hl, vl, dl, al]:
                        if line_length > 1:
                            if c == 1:
                                _p1Score += 2 ** (line_length-1)
                            else:
                                _p2Score += 2 ** (line_length-1)
                    # If all found lines are length 1, check if it is the special case of a lone piece
                    if hl == vl == dl == al == 1 and lone_piece:
                        if c == 1:
                            _p1Score += 1
                        else:
                            _p2Score += 1
        return (_p1Score, _p2Score)










    ## can be used once I want to play the game, but as for now I am making it strictly bot versus bot

    # # Convert a raw string to a command and a list of arguments
    # def process_command(self, s):
    #     s = s.lower().strip()
    #     if len(s) == 0:
    #         return True
    #     command = s.split(" ")[0]
    #     args = [x for x in s.split(" ")[1:] if len(x) > 0]
    #     if command not in self.command_dict:
    #         print("? Uknown command.\nType 'help' to list known commands.", file=sys.stderr)
    #         print("= -1\n")
    #         return False
    #     try:
    #         return self.command_dict[command](args)
    #     except Exception as e:
    #         print("Command '" + s + "' failed with exception:", file=sys.stderr)
    #         print(e, file=sys.stderr)
    #         print("= -1\n")
    #         return False
        
    # # Will continuously receive and execute commands
    # # Commands should return True on success, and False on failure
    # # Every command will print '= 1' or '= -1' at the end of execution to indicate success or failure respectively
    # def main_loop(self):
    #     while True:
    #         s = input()
    #         if s.split(" ")[0] == "exit":
    #             print("= 1\n")
    #             return True
    #         if self.process_command(s):
    #             print("= 1\n")

    # # List available commands
    # def help(self, args):
    #     for command in self.command_dict:
    #         if command != "help":
    #             print(command)
    #     print("exit")
    #     return True

    # # Helper function for command argument checking
    # # Will make sure there are enough arguments, and that they are valid integers
    # def arg_check(self, args, template):
    #     if len(args) < len(template.split(" ")):
    #         print("Not enough arguments.\nExpected arguments:", template, file=sys.stderr)
    #         print("Recieved arguments: ", end="", file=sys.stderr)
    #         for a in args:
    #             print(a, end=" ", file=sys.stderr)
    #         print(file=sys.stderr)
    #         return False
    #     for i, arg in enumerate(args):
    #         try:
    #             args[i] = int(arg)
    #         except ValueError:
    #             try:
    #                 args[i] = float(arg)
    #             except ValueError:
    #                 print("Argument '" + arg + "' cannot be interpreted as a number.\nExpected arguments:", template, file=sys.stderr)
    #                 return False
    #     return True