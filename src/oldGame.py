from game import Game
class OldGame(Game):
    """
    Ignore this class it does not do exactly what I wanted, changed all of game class private attributes to protected
    """
    def __init__(self, numRows:int, numCols:int, scoreCutoff:float, handicap:float, p1Path:str, p2Path:str):
        super()._init_(numRows, numCols, scoreCutoff, handicap, p1Path, p2Path)
    
    def __str__(self):
        '''
        show the board
        '''
        super()._str_()

    # want to eventually switch to my score calculation
    def _calcScore(self):
        """
        This function calculates the score from scratch given the current state by iterating over all lines for every direction

        Args:
            None

        Returns:
            int: Player 1 Score
            int: Player 2 Score
        """
        self._p1Score = 0
        self._p2Score = self._HANDICAP

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
                                self._p1Score += 2 ** (line_length-1)
                            else:
                                self._p2Score += 2 ** (line_length-1)
                    # If all found lines are length 1, check if it is the special case of a lone piece
                    if hl == vl == dl == al == 1 and lone_piece:
                        if c == 1:
                            self._p1Score += 1
                        else:
                            self._p2Score += 1
        return self._p1Score, self._p2Score
