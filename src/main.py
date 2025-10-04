from game import Game
from player import Player
from Players.randomPlayer import RandomPlayer
import time



if __name__ == "__main__":
    # rules for main
    delay = 0
    printGame = False
    
    # set rules for the game
    rows = 10
    cols = 10
    cutoff = 0
    handicap = 0.5

    # initialize the game
    p1 = RandomPlayer("kevin")
    p2 = RandomPlayer("marvin")


    while True:
        game = Game(rows, cols, cutoff, handicap, p1._classPath, p2._classPath)
        game.ignoreMirrorMatch = False
        while not game.gameOver():
            if printGame:
                print(p1.actionMove(game), "p1")
                print(game)
                time.sleep(delay)
                if not game.gameOver():
                    print(p2.actionMove(game), "p2")
                    print(game)
                    time.sleep(delay)
            else:
                p1.actionMove(game)
                if not game.gameOver():
                    p2.actionMove(game)

        game.save()     

