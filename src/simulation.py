from game import Game
from Players.player import Player
import time
import random
import os
import json

# made simulation class so that the player is able to know if it is his turn, also improves generalizability
# also was able to have settings to see if we want iterations or infinite
# but due to having a new quality to check if it is a new game, the player order does not matter for now

class Simulation:
    """
    Question: 
    [x] should the simulation handle the recording of games, or have the game record itself
        - simulation records| pros: can update less frequently for players to save time, simulation has access to p1 and p2 classes, game should only deal with playing itself and representing itself not controlling, cons: things that want to play using this simulation must abide by the saving patterns
    


    todo:
    [x] have setter for mirror match, recordGames, recordStats
    [ ] store the dictionary for many runs and then update them every once in a while say every 1000 runs 
    [ ] simulation saves the stats
    [ ] assure simulation saving makes it open ended and accessible

    """
    def __init__(self, startBoard:tuple, p1:Player, p2:Player, iterations:int=0, settings:tuple=(False, True, True, True, 0, 10000)):
        """
        Args:
            startBoard(numRows, numCols, scoreCutoff, handicap)
            p1 must be an object of subclass of Player
            p2 must be an object of subclas of Player
            iterations: 0 -> inf else n interations
            settings:(printGame, recordStats, recordGames, ignoreMirrorMatch, delay(in seconds, record interval))
        """

        # initialize gameSettings
        self._iterations = iterations
        self._settings = settings
        self._printGame = settings[0]
        self._recordStatistics = settings[1]
        self._recordGames = settings[2]
        self._ignoreMirrorMatch = settings[3]
        self._delay = settings[4]
        self._recordInterval = settings[5]
        self._p1 = p1
        self._p2 = p2
        self._startBoard = startBoard

        
    def run(self):
        # if iterations = 0 then go for infinity, if iterations does not equal 0 then go until count = iterations
        count = 0
        while not self._iterations or count < self._iterations:
            # randomly flit which player goes first or second
            # fixed error of before the update paths for who went first or second would be wrong
            num = random.random()
            if num < 0.5:
                tmp = self._p1
                self._p1 = self._p2
                self._p2 = tmp

            # create a new game of the same type and settings
            self._game = Game(self._startBoard[0], self._startBoard[1], self._startBoard[2], self._startBoard[3], self._p1.getClassPath(), self._p2.getClassPath())
            self._game.setRecordStats(self._settings[1])
            self._game.setRecordGames(self._settings[2])
            self._game.setIgnoreMirrorMatch(self._settings[3])
        
            # give the players references to the game and set their order since it is a new game
            self._p1.setGame(self._game, 1)
            self._p2.setGame(self._game, 2)

            # run an episode
            while not self._game.gameOver():
                if self._printGame:
                    # print the type of the players, and move then the game
                    print(f"p1: {type(self._p1).__name__} | p2: {type(self._p2).__name__}")
                    print(self._p1.actionMove(), "p1")
                    print(self._game)
                    time.sleep(self._delay)
                    if not self._game.gameOver():
                        # print the type of the players, and move then the game
                        print(f"p1: {type(self._p1).__name__} | p2: {type(self._p2).__name__}")
                        print(self._p2.actionMove(), "p2")
                        print(self._game)
                        time.sleep(self._delay)
                else:
                    self._p1.actionMove()
                    if not self._game.gameOver():
                        self._p2.actionMove()

            if self._recordStatistics:
                self._saveGame()
                if not (count+1)%self._recordInterval:
                    self._savePlayerStats()
            count += 1


    def _saveGame(self):
        """
        When the game is over store the stats for that given game in a json files
        no need to read only write
        """
        # it is only called when the game is over
        # ignore matches where it plays each other since it will always win and lose
        p1Class = type(self._p1).__name__
        p2Class = type(self._p2).__name__
        mirror = p1Class == p2Class
        if mirror and self._ignoreMirrorMatch:
            print("This is a mirror match and we wish to ignore them!")
            return
        

        if type(self._p1).__name__ == p1Class:
            p1Order = 1
            p2Order = 2

        else:
            p1Order = 2
            p2Order = 1
        
        # update stats for player 1 
        self._updatePlayerStats(self._p1._stats, p2Class, p1Order)
    
        # update stats for player 2
        self._updatePlayerStats(self._p2._stats, p1Class, p2Order)
        
        
        # record the stats of a game
        if self._recordGames:
            won = self._game.getWinner()
            gamePath = f"../statistics/games/{p1Class}vs{p2Class}"
            os.makedirs(gamePath, exist_ok=True)
            with open((gamePath + "/" + self._game.getId() + ".json"), "w") as file:
                if won == 1:
                    winner = p1Class
                elif won == 2:
                    winner = p2Class
                else:
                    assert won != 0, "game is over but no winner"    
                init = self._game.getInit()
                moveHistory = self._game.getMoveHistory()
                _gameStats = {"id": self._game.getId(), "class1": p1Class, "class2": p2Class, "winner": won, "winnerType": winner, "numberMoves": moveHistory[1], "scores":self._game.getPlayerScores(), "initialGame": {"numRows":  init[0], "numCols":  init[1], "scoreCutoff": init[2], "handicap": init[3]}, "finalBoard": self._game.getBoard(),"moveHistory": moveHistory[0]}
                file.seek(0)
                json.dump(_gameStats, file)
                file.truncate()


    def _updatePlayerStats(self, _stats:dict, oppClass:str, playerOrder)-> None:
        """
        when the game is over store the stats for the player in the local dictionaries but does not do anything with file management

        args:
            oppClass: the type of the opponent
            _stats: the dictionary of the stats to be saved
            playerOrder: is it p1 or p2 being saved
        """
        # can be good to keep stats of mirror matches to decide if there is a favouritism to be player 1 or 2
        won = self._game.getWinner()

        # update the stats for the game just played
        _stats["gamesPlayed"] += 1

        # check if first time facing opponent if so initialize key
        if oppClass not in _stats["winningVS"].keys():
            _stats["winningVS"][oppClass] = { "gamesPlayed" : 0, "gamesWon":0, "gamesLost":0, "gamesWonAsP1": 0, "gamesWonAsP2":0, "gamesList":[] }
        # update game aginast opp
        _stats["winningVS"][oppClass]["gamesPlayed"] += 1

        # record winnings
        if won == playerOrder:
            _stats["gamesWon"] += 1
            _stats[f"gamesWonAsP{playerOrder}"] += 1
            _stats["winningVS"][oppClass]["gamesWon"] += 1
            _stats["winningVS"][oppClass][f"gamesWonAsP{playerOrder}"] += 1
        else:
            assert won != 0, "there is no winner when there should be"
            _stats["gamesLost"] += 1
            _stats["winningVS"][oppClass]["gamesLost"] += 1
        
        # record the id of the game
        if self._recordGames:
            _stats["winningVS"][oppClass]["gamesList"].append(self._game.getId())


    def _savePlayerStats(self):
        """
        write the player stats for the simulation
        """
        # save p1 stats
        with open(self._p1.getClassPath(), "r+") as file:
            file.seek(0)
            json.dump(self._p1._stats, file)
            file.truncate()

        # save p2 stats
        with open(self._p2.getClassPath(), "r+") as file:
            file.seek(0)
            json.dump(self._p2._stats, file)
            file.truncate()
