from datetime import datetime
from player import Player
import os
import json
import sys


"""
todo:
[x] make w+ into r+ by checking first if the file exists or not
[x] edit id so that it is only : separated numbers
[] make it so that the players wins and losses are divided by who he beat as well, record against opponent (should be a dict to key in opponent)
[] get current working directory to calculate path to store the statistics as for now must be run in src

tasks:
[] test my game to find the bug with my score calculation
[] update calc score so that it is more efficient using my algorithm


maybe:
[] make it so that the description of the player is shown in the game logs and player logs
"""

class Game:
    """
    The game class is a representation of the environment in which __players are able to interact with.
    This includes holding game state as well as provides functionality to make actions

    Actions:
    play: plays a move
    getScore: gets the current score of the game state
    isLegal: checks if a given move is legal
    winner: says if the board is over and someone has won, 0 = nobody, 1 = __player 1, 2 = __player 2
    undo: allows to roll back the game state
    """    
    ## does python always pass by reference?
    def __init__(self, numRows:int, numCols:int, scoreCutoff:float, handicap:float, p1Path:str, p2Path:str):
        # generate id based on time of initializaiton
        # Current time
        now = datetime.now()
        # Format: YYYY-MM-DD HH:MM:SS.mmm
        self.__id = now.strftime("%Y_%m_%d_%H_%M_%S_") + f"{int(now.microsecond/1000):08d}" 
        # Game state  
        # all caps = const
        self.__NUMCOLS = int(numCols)
        self.__NUMROWS = int(numRows)
        self.__SCORECUTOFF = float(scoreCutoff)
        self.__NUMTILES = self.__NUMCOLS * self.__NUMROWS
        self.__HANDICAP = float(handicap)
        self.__won = 0
        self.__numMoves = 0
        self.__moveHistory = [] #((row:int,col:int),(p1score:float, p2score:float), cur__player:int, winner:int)
        self.__currentPlayer = 0 # 0 __player 1 or 1 __player 2
        self.__p1Score = int(0)
        self.__p2Score = float(handicap)

        # needed for my efficient implementation of __calcScore
        # self.matrixLines = [[[0 for _ in range(4)] for _ in range(self.__NUMCOLS)] for _ in range(self.__NUMROWS)] #[/, \, |, -]

        # which board version is correct?
        #self.__board= [[0 for _ in range(self.__NUMCOLS)] for _ in range(self.__NUMROWS)] #if wanting to use regular list
        self.__board= []
        for _ in range(self.__NUMROWS):
            self.__board.append([0]*self.__NUMCOLS)

        # store the players
        self.__p1ClassPath = p1Path
        self.__p2ClassPath = p2Path
        # recording mariables
        self.ignoreMirrorMatch = True
        self.showStatistics = True
        self.recordGames = True

    def __str__(self):
        '''
            show the board
        '''
        output = str()
        for row in self.__board:
            output += " ".join(["_" if v == 0 else str(v) for v in row]) + "\n"
        output += f"\nplayer 1 has score: {self.__p1Score} \nplayer 2 has score: {self.__p2Score}"
        if self.__won != 0:
            output += "\n" + f"***game over: winner is {self.__won}***"
        
        return output + "\n__________________________________\n"

    def getId(self) -> str:
        """
        returns the id for a given game
        """
        return self.__id

    # getters since we do not want any setters as the board should only be manipulated through the play function
    def getBoard(self) -> list:
        """
        return: board state, list of lists
        """
        return self.__board
        ## does this return a reference or the actual board

    def getWinner(self) -> int:
        """
        return:
        1: player 1 won
        2: player 2 won
        0: no winnner yet
        """
        self.gameOver()
        return self.__won
    
    def getInit(self)->tuple:
        """
        returns (numRows, numCols, scoreCutoff, Handicap)
        """
        return (self.__NUMROWS, self.__NUMCOLS, self.__SCORECUTOFF, self.__HANDICAP)
    
    def getMoveHistory(self) -> tuple:
        """
        return:
        tuple:
        index 0:
        move history list ((row:int,col:int),(p1score:float, p2score:float), cur__player:int, winner:int)
        index 1:
        len of move history
        """
        return (self.__moveHistory, self.__numMoves)
    
    def getPlayerScores(self) -> tuple:
        """
        return: (player1Score, Player2Score)
        """
        self.__calcScore()
        return (self.__p1Score, self.__p2Score)

    def getCurrentPlayer(self):
        """
        return: the current player 
        0 = player 1 
        1 = player 2
        """
        return self.__currentPlayer

    def getPossibleMoves(self) -> list:
        """
        return: list(all spaces that have no stones)
        """
        moves = []
        for y in range(self.__NUMROWS):
            for x in range(self.__NUMCOLS):
                if self.__board[y][x] == 0:
                    moves.append((x, y))
        return moves
    
    
    def playMove(self, row, col) -> int:
        '''
            >> play <col> <row>
            Places the current __player's piece at position (<col>, <row>). Check if the move is legal before playing it.
            can return false if the move is illegal

        return:
        -1 if illegal move
        1 if move successful 
        2 if there is a winner
        '''
        if not self.isLegal(row, col):
            return -1
        if self.__won != 0:
            return 2

        ## could these be assertions, or then this would stop the program which is not what I want

        # update the board state
        if self.__currentPlayer:
            self.__board[row][col] = 2
            self.__currentPlayer = 0
        else:
            self.__board[row][col] = 1
            self.__currentPlayer = 1
    
        # calculate the score through all the four possible directions of lines
        self.__calcScore() # does not currently need arguments

        # keep trach of the number of moves played
        self.__numMoves += 1 

        self.gameOver()

        # add the move history to the list for undo
        self.__moveHistory.append(((row,col),(self.__p1Score, self.__p2Score), self.__currentPlayer, self.__won))

        return 1


    def isLegal(self, row:int, col:int)->bool:
        """
        return:
        True if move is legal
        False if move is illegal
        """
        if self.__won == 0 and self.__board[row][col] == 0:
            return True
        
        return False

    def undo(self, args):
        '''
        >> undo
        Undoes the last move.
        return:
        True if undo was successful
        False if no moves to undo
        '''
        if not self.__moveHistory:
            return False
        
        status = self.__moveHistory.pop()
        self.__numMoves -= 1
        self.__board[status[0][0]][status[0][1]] = 0
        if self.__moveHistory:
            newState = self.__moveHistory[-1]
            self.__p1Score = newState[1][0]
            self.__p2Score = newState[1][1]
            self.__currentPlayer = newState[2]
            self.__won = newState[3]
        else:
            self.__numMoves = 0
            self.__p1Score = 0
            self.__p2Score = self.HANDICAP
            self.__currentPlayer = 1
            self.__won = 0
        return True

    def gameOver(self)-> bool:
        """
        Updates the winner if there is one

        return:
        True if the game is over
        False if the game is not over
        """
        if self.__p1Score >= self.__SCORECUTOFF and self.__SCORECUTOFF != 0:
            self.__won = 1
            return True
        elif self.__p2Score >= self.__SCORECUTOFF and self.__SCORECUTOFF != 0:
            self.__won = 2
            return True
        elif self.__numMoves == self.__NUMTILES:
            if self.__p1Score > self.__p2Score:
                self.__won = 1
            else:
                self.__won = 2 
            return True
        else:
            self.__won = 0
        assert self.__numMoves <= self.__NUMTILES, "number of tiles exceed possible"
        return False


    # want to eventually switch to my score calculation
    def __calcScore(self):
        self.__p1Score = 0
        self.__p2Score = self.__HANDICAP

        # Progress from left-to-right, top-to-bottom
        # We define lines to start at the topmost (and for horizontal lines leftmost) point of that line
        # At each point, score the lines which start at that point
        # By only scoring the starting points of lines, we never score line subsets
        for y in range(self.__NUMROWS):
            for x in range(self.__NUMCOLS):
                c = self.__board[y][x]
                if c != 0:
                    lone_piece = True # Keep track of the special case of a lone piece
                    # Horizontal
                    hl = 1
                    if x == 0 or self.__board[y][x-1] != c: #Check if this is the start of a horizontal line
                        x1 = x+1
                        while x1 < self.__NUMCOLS and self.__board[y][x1] == c: #Count to the end
                            hl += 1
                            x1 += 1
                    else:
                        lone_piece = False
                    # Vertical
                    vl = 1
                    if y == 0 or self.__board[y-1][x] != c: #Check if this is the start of a vertical line
                        y1 = y+1
                        while y1 < self.__NUMROWS and self.__board[y1][x] == c: #Count to the end
                            vl += 1
                            y1 += 1
                    else:
                        lone_piece = False
                    # Diagonal
                    dl = 1
                    if y == 0 or x == 0 or self.__board[y-1][x-1] != c: #Check if this is the start of a diagonal line
                        x1 = x+1
                        y1 = y+1
                        while x1 < self.__NUMCOLS and y1 < self.__NUMROWS and self.__board[y1][x1] == c: #Count to the end
                            dl += 1
                            x1 += 1
                            y1 += 1
                    else:
                        lone_piece = False
                    # Anit-diagonal
                    al = 1
                    if y == 0 or x == self.__NUMCOLS-1 or self.__board[y-1][x+1] != c: #Check if this is the start of an anti-diagonal line
                        x1 = x-1
                        y1 = y+1
                        while x1 >= 0 and y1 < self.__NUMROWS and self.__board[y1][x1] == c: #Count to the end
                            al += 1
                            x1 -= 1
                            y1 += 1
                    else:
                        lone_piece = False
                    # Add scores for found lines
                    for line_length in [hl, vl, dl, al]:
                        if line_length > 1:
                            if c == 1:
                                self.__p1Score += 2 ** (line_length-1)
                            else:
                                self.__p2Score += 2 ** (line_length-1)
                    # If all found lines are length 1, check if it is the special case of a lone piece
                    if hl == vl == dl == al == 1 and lone_piece:
                        if c == 1:
                            self.__p1Score += 1
                        else:
                            self.__p2Score += 1



    def save(self):
        # save the states of the game if it finished
        if self.gameOver() and self.showStatistics:
            # ignore matches where it plays each other since it will always win and lose
            mirror = self.__p1ClassPath == self.__p2ClassPath
            if mirror and self.ignoreMirrorMatch:
                print("This is a mirror match and we wish to ignore them!")
                return
            
            p1 = self.__p1ClassPath.split("/")[-1].removesuffix(".json")
            p2 = self.__p2ClassPath.split("/")[-1].removesuffix(".json")
            # update stats for player 1
            self.__recordPlayerStats(self, self.__p1ClassPath, 1, p2)
        
            # update stats for player 2
            self.__recordPlayerStats(self, self.__p2ClassPath, 2, p1)
            
            
            # record the stats of a game
            if self.recordGames:
                os.makedirs("../statistics/games/{p1}vs{p2}", exist_ok=True)
                with open((f"../statistics/games/{p1}vs{p2}/{self.__id}.json"), "w") as file:
                    __p1Class = self.__p1ClassPath.split("/")[-1].removesuffix(".json")
                    __p2Class = self.__p2ClassPath.split("/")[-1].removesuffix(".json")
                    if self.__won == 1:
                        winner = self.__p1ClassPath.split("/")[-1].removesuffix(".json")
                    elif self.__won == 2:
                        winner = self.__p2ClassPath.split("/")[-1].removesuffix(".json")
                    else:
                        assert self.__won != 0, "game is over but no winner"    
                    init = self.getInit()
                    moveHistory = self.getMoveHistory()
                    __gameStats = {"id": self.getId(), "class1": __p1Class, "class2": __p2Class, "winner": self.getWinner(), "winnerType": winner, "numberMoves": moveHistory[1], "moveHistory": moveHistory[0], "scores":self.getPlayerScores(), "finalBoard": self.getBoard(), "initialGame": {"numRows":  init[0], "numCols":  init[1], "scoreCutoff": init[2], "handicap": init[3]}}
                    file.seek(0)
                    self.__dump_dicts_with_flat_lists(__gameStats, file)
                    file.truncate()


    def __recordPlayerStats(self, path:str, playerOrder:int, oppClass:str)-> None:
        # can be good to keep stats of mirror matches to decide if there is a favouritism to be player 1 or 2
        __stats = None
        if path:
            __pClass = path.split("/")[-1].removesuffix(".json")
            # if the file does not exist make the file
            if not os.path.exists(path):
                with open(path, "a") as file:
                    # check if the file is empty, if so create a new dict
                    __stats = {"class": __pClass, "gamesPlayed": 0, "gamesWon": 0, "gamesLost":0, "gamesWonAsP1": 0, "gamesWonAsP2":0, "winning" : {"opponentClass": oppClass, "gamesWon":0, "gamesLost":0, "gamesWonAsP1": 0, "gamesWonAsP2":0, "gamesList":[]}}
            
            
            # open the file to read than write 
            with open(path, "r+") as file:
                if not __stats:
                    __stats = json.load(file)
                # update the stats for the game just played
                __stats["gamesPlayed"] += 1
                __stats["winning"]["opponent"] = oppClass
                __stats["winning"]["gamesPlayed"] += 1
                if self.__won == playerOrder:
                    __stats["gamesWon"] += 1
                    __stats[f"gamesWonAsP{playerOrder}"] += 1
                    __stats["winning"]["gamesWon"] += 1
                    __stats["winning"][f"gamesWonAsP{playerOrder}"] += 1
                else:
                    assert self.__won != 0, "there is no winner when there should be"
                    __stats["gamesLost"] += 1
                    __stats["winning"]["gamesLost"] += 1
                
                __stats["winning"]["gamesList"].append(self.__id)
                file.seek(0)
                self.__dump_dicts_with_flat_lists(__stats, file)
                file.truncate()
            


    def __dump_dicts_with_flat_lists(self, obj, file, indent=4):
        """
        Dumps a dictionary to JSON:
        - Dictionaries are indented
        - Lists are kept on a single line
        Works recursively for nested dicts.
        """

        def __encode(obj, level=0):
            spacing = " " * (level * indent)
            if isinstance(obj, dict):
                items = []
                for k, v in obj.items():
                    key = json.dumps(k)
                    if isinstance(v, dict):
                        value = "".join(__encode(v, level + 1))
                    elif isinstance(v, list):
                        # Keep list on one line
                        value = json.dumps(v)
                    else:
                        value = json.dumps(v)
                    items.append(f"{spacing}{' ' * indent}{key}: {value}")
                return ["{\n" + ",\n".join(items) + f"\n{spacing}}}"]
            else:
                return [json.dumps(obj)]

        file.write("".join(__encode(obj)))



















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