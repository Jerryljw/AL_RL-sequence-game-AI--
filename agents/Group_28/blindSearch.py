# INFORMATION ------------------------------------------------------------------------------------------------------- #

# Author:  Jiawei Luo, Yifan Deng, Xinzhe Wang
# Date:    05/25/2021
# Purpose: Implementing Blind Search in agent of the Sequence Game
# Others: This file contains one uniform cost search(expolring whole board), one ucs(exploring in four directions), 
#         one normal minimax(not working at all but can be report materials:))

# IMPORTS ------------------------------------------------------------------------------------------------------------#
from template import Agent
import heapq, random
import math
from Sequence.sequence_model import *

class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)

    def SelectAction(self, actions, game_state):

        # ucs Advanced
        action = self.uscSelectionA(actions, game_state)
        
        # ucs
        # action = self.uscSelection(actions, game_state)

        # minimax
        # action = self.minimaxSelection(actions, game_state, True, 2)
        return action

    # UCS Advanced ------------------------------------------------------------------------------------------------#
    def uscSelectionA(self, actions, game_state):
        nextAction = random.choice(actions)

        minScore = math.inf
        for action in actions:
            score = self.uscActionsA(action, game_state)
            if minScore > score:
                minScore = score
                nextAction = action

        return nextAction

    #  mini distance between one of the possible action and the goal
    def uscActionsA(self, action, game_state):
        if action["type"] == "trade":
            return math.inf
        point = action["coords"]
        point1s = []
        minDistance = math.inf
        awesomeSet = set()
        awesomeSet.update(((4, 4), (4, 5), (5, 4), (5, 5), (0, 0), (0, 9), (9, 9), (9, 0)))

        # if the agent one before it has no last action, means it is the first one
        # then we need to find the closest distance between 4 hearts/4 corner with
        # all the possible actions
        if game_state.agents[(self.id - 1) % 4].last_action == None:
            point1s = list(awesomeSet)
            minDistance = min(self.chipDistanceA(point, point1s), minDistance)
            print("first: ", minDistance)
            return minDistance
        else:
            color = game_state.agents[self.id].colour
            seqColor = game_state.agents[self.id].seq_colour
            chips = game_state.board.chips

            # get the current position of same color chips and JOKER and empty 4 Hearts
            for x in range(len(chips)):
                for y in range(len(chips[0])):
                    if chips[x][y] == color or chips[x][y] == seqColor:
                        point1s.append((x, y))
                    if (x, y) in awesomeSet and chips[x][y] == EMPTY:
                        point1s.append((x, y))

            # try to get closer with same color chips or JOKER or 4 Hearts
            # consider the obstacle(opp_color) in the way, and four directions
            minDistance = min(self.chipDistanceA(point, point1s), minDistance)
            return minDistance

    # the minimum distance between point and one of the point in point1s
    def chipDistanceA(self, point, point1s):
        myqueue = PriorityQueue()
        startCost = 0
        parentPoint = (-1, -1)
        startNode = (parentPoint, point, startCost)
        # TODO: push the initial node into the queue, with F(n)
        myqueue.push(startNode, startCost)
        # create a visited-node set
        visited = set()
        # a dict to store the best g_cost
        best_g = {}
        totalCost = 0
        expandTime = 0

        while myqueue:
            node = myqueue.pop()
            print(node)
            expandTime += 1
            parent, pos, cost = node
            # take out the best cost for current pos
            best = best_g.setdefault(pos, cost)

            # check if the node has been visited, or need to reopen
            if pos not in visited or cost < best:
                best_g.update({pos: cost})
                if pos in point1s:
                    totalCost = cost
                    break

                if expandTime == 1:
                    succNodes = self.expandA(parent, pos, True)
                else:
                    succNodes = self.expandA(parent, pos, False)
                if succNodes == []:
                    return math.inf
                for succNode in succNodes:
                    succParent, succPos, succCost = succNode
                    newNode = (succParent,succPos, cost + succCost)
                    myqueue.push(newNode, cost + succCost)
        return totalCost

    def expandA(self, parentPoint, point, isRoot):
        x0, y0 = parentPoint
        x, y = point

        # expand 8 directions
        if isRoot:
            smallSeqs = [[(-1, 0), (0, 0), (1, 0)],
                         [(0, -1), (0, 0), (0, 1)],
                         [(-1, -1), (0, 0), (1, 1)],
                         [(-1, 1), (0, 0), (1, -1)]]
            children = []
            for seq in smallSeqs:
                for i in range(len(seq)):
                    dx, dy = seq[i]
                    if x + dx >= 0 and x + dx < 10 and y + dy >= 0 and y + dy < 10:
                        if not (dx == dy and dx == 0):
                            children.append((point, (x + dx, y + dy), 1))
        else:
            # only expand one direction
            children = []
            dx = x - x0
            dy = y - y0
            if x+dx>=0 and x + dx < 10 and y + dy >= 0 and y + dy < 10:
                children.append((point, (x + dx, y + dy), 1))
        return children
    
    # USC ------------------------------------------------------------------------------------------------#

    def uscSelection(self, actions, game_state):
        nextAction = random.choice(actions)

        minScore = math.inf
        for action in actions:
            score = self.uscActions(action, game_state)
            if minScore > score:
                minScore = score
                nextAction = action
        return nextAction

    #  mini distance between one of the possible action and the goal
    def uscActions(self, action, game_state):
        point = action["coords"]

        point1s = []
        minDistance = math.inf
        
        # if the agent one before it has no last action, means it is the first one
        # then we need to find the closest distance between 4 hearts/4 corner with
        # all the possible actions
        if game_state.agents[(self.id - 1) % 4].last_action == None:
            goalSet = set()
            goalSet.update(((4, 4), (4, 5), (5, 4), (5, 5), (0, 0), (0, 9), (9, 9), (9, 0)))
            point1s = list(goalSet)
            minDistance = min(self.chipDistance(point, point1s), minDistance)
            print("first: ",minDistance)
            return minDistance
        else:
            color = game_state.agents[self.id].colour
            seqColor = game_state.agents[self.id].seq_colour
            chips = game_state.board.chips
            for x in range(len(chips)):
                for y in range(len(chips[0])):
                    if chips[x][y] == color or chips[x][y] == seqColor or chips[x][y] == "#":
                        point1s.append((x, y))
            minDistance = min(self.chipDistance(point, point1s), minDistance)
            return minDistance

    def chipDistance(self, point, point1s):
        myqueue = PriorityQueue()
        startCost = 0
        startNode = (point, startCost)
        # TODO: push the initial node into the queue, with F(n)
        myqueue.push(startNode,startCost)
        # create a visited-node set
        visited = set()
        # a dict to store the best g_cost
        best_g = {}
        totalCost = 0

        while myqueue:
            node = myqueue.pop()
            pos, cost = node
            # take out the best cost for current pos
            best = best_g.setdefault(pos, cost)

            # check if the node has been visited, or need to reopen
            if pos not in visited or cost < best:
                best_g.update({pos: cost})
                if pos in point1s:
                    print("stop")
                    totalCost = cost
                    break

                succNodes = self.expand(pos)
                for succNode in succNodes:
                    succPos, succCost = succNode
                    newNode = (succPos, cost + succCost)
                    myqueue.push(newNode, cost + succCost)
        return totalCost
    
    # expand the eight node around current position
    def expand(self, point):
        x, y = point
        smallSeqs = [[(-1, 0), (0, 0), (1, 0)],
                [(0, -1), (0, 0), (0, 1)],
                [(-1, -1), (0, 0), (1, 1)],
                [(-1, 1), (0, 0), (1, -1)]]
        children = []
        for seq in smallSeqs:
            for i in range(len(seq)):
                dx, dy = seq[i]
                if x + dx >= 0 and x + dx < 10 and y + dy >= 0 and y + dy < 10:
                    if not(dx==dy and dx==0):
                        children.append(((x+dx, y+dy), 1))
                        
        return children
    
    # minimax ------------------------------------------------------------------------------------------------#
    def minimaxSelection(self, actions, game_state, is_max, depth=4):
        # a Board with weighted value
        weightBoard = self.weightedBoard()

        # try to get an initial action which is randomly chosen
        nextAction = random.choice(actions)
        # best Score
        bestScore = - math.inf

        # get current state of board, which pos is empty 10*10 matrix
        chips = game_state.board.chips
        for action in actions:

            x = action["coords"][0]
            y = action["coords"][1]
            if (chips[x][y] == "_"):
                color = game_state.agents[self.id].colour
                chips[x][y] == color
                score = self.minimax(actions, game_state, weightBoard, -math.inf, math.inf, not is_max, depth - 1)
                chips[x][y] == "_"
                if (score > bestScore):
                    bestScore = score
                    nextAction = action
        return nextAction

    def minimax(self, actions, game_state, weightBoard, alpha, beta, is_max, depth):
        chips = game_state.board.chips
        if (depth == 0):
            return -self.evaluation(game_state, weightBoard)

        # current agent wants to win
        if (is_max):
            bestScore = -math.inf
            for action in actions:
                x = action["coords"][0]
                y = action["coords"][1]
                if (chips[x][y] == "_"):
                    color = game_state.agents[self.id].colour
                    chips[x][y] == color
                    score = self.minimax(actions, game_state, weightBoard, alpha,
                                         beta, not is_max, depth - 1)
                    chips[x][y] == "_"
                    bestScore = max(bestScore, score)
                    alpha = max(alpha, bestScore)
                    if beta <= alpha:
                        return bestScore

            return bestScore
        else:
            bestScore = math.inf

            for action in actions:
                x = action["coords"][0]
                y = action["coords"][1]
                if (chips[x][y] == "_"):
                    color = game_state.agents[self.id].colour
                    chips[x][y] == color
                    score = self.minimax(actions, game_state, weightBoard, alpha,
                                         beta, not is_max, depth - 1)
                    chips[x][y] == "_"
                    bestScore = min(bestScore, score)
                    beta = min(beta, bestScore)
                    if beta <= alpha:
                        return bestScore
            return bestScore

    # evaluation of Board, calculating the value of whole board
    def evaluation(self, game_state, weightBoard):
        # default value for chips and sequence
        val = 1
        seqVal = 5
        oppVal = -1
        oppSeqVal = -5

        evaluation = 0
        color = game_state.agents[self.id].colour
        seqColor = game_state.agents[self.id].seq_colour
        oppColor = game_state.agents[self.id].opp_colour
        oppSeqColor = game_state.agents[self.id].opp_seq_colour

        chips = game_state.board.chips

        # go through the whole current board with chips on it
        for i in range(len(chips)):
            for j in range(len(chips[0])):
                if chips[i][j] == color:
                    evaluation += weightBoard.get((i, j)) * val
                if chips[i][j] == seqColor:
                    evaluation += weightBoard.get((i, j)) * seqVal
                if chips[i][j] == oppColor:
                    evaluation += weightBoard.get((i, j)) * oppVal
                if chips[i][j] == oppSeqColor:
                    evaluation += weightBoard.get((i, j)) * oppSeqVal

        return evaluation

    # a function to find the cards position in the board
    # TODO: This is only using coords in actions to find the cards actions
    def cardPosition(self, card, actions):
        pos = set()
        for action in actions:
            if action['play_card'] == card:
                pos.add(action['coords'])
        return pos

    # a dictionary maps coordinates and weight
    def weightedBoard(self):
        weightBoard = {}
        for row in range(10):
            for col in range(10):
                # initial all the coords
                weightBoard.update({(row, col): 1})
                # give them a weight 2 since they are in the line with unimelb
                if row == 0 or row == 9 or col == 0 or col == 9:
                    weightBoard.update({(row, col): 20})
                if col == row or row == 9 - col:
                    weightBoard.update({(row, col): 20})
        # change the weight of the 4 key position to 10
        weightBoard.update({(4, 4): 100})
        weightBoard.update({(4, 5): 100})
        weightBoard.update({(5, 4): 100})
        weightBoard.update({(5, 5): 100})

        return weightBoard

# Helper Class ------------------------------------------------------------------------------------------------#
class PriorityQueue:
    """
      Lowest cost priority queue data structure.
    """

    def __init__(self):
        self.heap = []
        self.count = 0

    def push(self, item, priority):
        entry = (priority, self.count, item)
        heapq.heappush(self.heap, entry)
        self.count += 1

    def pop(self):
        (_, _, item) = heapq.heappop(self.heap)
        return item

    def isEmpty(self):
        return len(self.heap) == 0

    def update(self, item, priority):
        # If item already in priority queue with higher priority, update its priority and rebuild the heap.
        # If item already in priority queue with equal or lower priority, do nothing.
        # If item not in priority queue, do the same thing as self.push.
        for index, (p, c, i) in enumerate(self.heap):
            if i == item:
                if p <= priority:
                    break
                del self.heap[index]
                self.heap.append((priority, c, item))
                heapq.heapify(self.heap)
                break
        else:
            self.push(item, priority)
