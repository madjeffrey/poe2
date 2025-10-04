import json
class Player:
    """
    This is a template super class for a given player that will implement a given stategy
    it must update the function actionMove() returning the coordinates of its next move
    """
    # the description must describe the strategy of the player
    
    # the class path holds the path to the json file of the stats for a given player strategy

    def __init__(self, name="bot"):
        self._name = name
        self._classPath = "../statistics/classes/" + str(self.__class__).split(".")[-1].replace("'>", ".json")
        assert self._classPath, "class does not have a path to the class statistics"
        assert self._desc, "class does not have a description"


    def actionMove(self)->tuple:
        """
        This is the most important function that 
        returns a tuple of a row and col of the decision 
        of the players next move
        (-69, -69) means not implemented
        """
        return (-69, -69)
    
    def __str__(self):
        return f"Hello I am player {self.__name}, my strategy is: {self.__desc}"
    

