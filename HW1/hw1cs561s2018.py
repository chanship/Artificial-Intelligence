
"""
This is homework #1 for A.I. spring class CSCI561

Simple checker game by adopting Minimax, Alphabeta Algorithm

- __main file__ -> class: starCircleWar
- methods:
    * parseInputFile
    * run_minimax
    * run_alphabeta

input : input.txt
output : output.txt
    - nextMove
    - myopic utility value
    - farsighted utility value
    - total node expansion count
"""

__version__ = '0.8'
__author__ = 'Chanshin Peter Park'

import logging

from Minimax import Minimax
from Board import Board
from AlphaBeta import AlphaBeta


class starCircleWar(object):

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

        input_file = "input.txt"
        param = self.parseInputFile(input_file)

        self.initialBoardState = param["CURRENT_BOARD_STATE"]
        self.maxplayer = param["PLAYER"]
        self.depth = param["DEPTH_LIMIT"]
        self.row_values = param["ROW_VALUES"]
        self.algorithm = {"MINIMAX": 0, "ALPHABETA": 1}[param["ALGORITHM"]]

        #Initialize Gaming Board
        self.Board = Board(self.initialBoardState, self.row_values, self.maxplayer, None, 0, 0, 0, 0, self.maxplayer)

        # Play Game
        if self.algorithm == 0:
            self.run_minimax()
        elif self.algorithm == 1:
            self.run_alphabeta()

    @staticmethod
    def parseInputFile(input_file):
        param = {}
        rfile = open(input_file)

        param["PLAYER"] = rfile.readline().strip()
        param["ALGORITHM"] = rfile.readline().strip()
        param["DEPTH_LIMIT"] = rfile.readline().strip()

        # boardState : state of starting board
        boardState = [[0]*8 for i in range(8)]
        for i in range(8):
            boardState[i] = list(rfile.readline().rstrip().split(','))
        param["CURRENT_BOARD_STATE"] = boardState

        # row_values : weight of each row
        row_values = list(rfile.readline().rstrip().split(','))
        param["ROW_VALUES"] = row_values

        return param

    def run_minimax(self):
        game = Minimax(self.Board, self.maxplayer, self.depth)
        bestscore = game.minimax(game.Board,0)
        #print bestscore

        if bestscore.PrevX == bestscore.X and bestscore.PrevX == bestscore.Y:
            game.nextMove = "pass"
        else:
            game.nextMove = bestscore.interpret_xy(bestscore.PrevX, bestscore.PrevY) + "-" + bestscore.interpret_xy(bestscore.X, bestscore.Y)
        game.util_myopic = bestscore.get_eval(bestscore.boardState)

        # print "nextMove:" + game.nextMove
        # print "myopic:" + str(game.util_myopic)
        # print "farsighted : " + str(game.util_farsighted)
        # print "nodeCount:" + str(game.node_count)
        game.print_nextState(game.nextMove,game.util_myopic,game.util_farsighted,game.node_count)

    def run_alphabeta(self):
        game = AlphaBeta(self.Board, self.maxplayer, self.depth)
        # print game.path
        # for i in range(len(game.path)):
        #      print game.path[i]

        first = game.path.pop(len(game.path)-1)

        if isinstance(first,Board) != 1:
            game.nextMove = first[0]
            game.util_myopic = first[1]
        else:
            if first.PrevX == first.X and first.PrevX == first.Y:
                game.nextMove = "pass"
            else:
                game.nextMove = first.interpret_xy(first.PrevX, first.PrevY) + "-" + first.interpret_xy(
                    first.X, first.Y)
            game.util_myopic = first.get_eval(first.boardState)

        if self.maxplayer == 'Star':
            game.util_farsighted = game.alpha
        else:
            game.util_farsighted = game.beta
        # print "nextMove:" + game.nextMove
        # print "myopic:" + str(game.util_myopic)
        # print "farsighted : " + str(game.util_farsighted)
        # print "nodeCount:" + str(game.node_count)
        game.print_nextState(game.nextMove,game.util_myopic,game.util_farsighted,game.node_count)

if __name__ == '__main__':
    starCircleWar()
#game.parseInputFile('input.txt')