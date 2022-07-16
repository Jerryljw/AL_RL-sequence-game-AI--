# INFORMATION ------------------------------------------------------------------------------------------------------- #

# Author:  Jiawei Luo, Yifan Deng, Xinzhe Wang
# Date:    05/25/2021
# Purpose: Implementing Advanced Heuristic Search in agent of the Sequence Game
# Others: An agent based on uniform search. First, to find if we choose action A,
#         how much will it cost. "Cost" here means that the distance between the 
#         position we just take and the same color chip. And the search is not 
#         exploring the whole board, but only the four directions of current position.
#         Once we got the closest position, we use the same method to find the best
#         draft card and then choose this action.

# IMPORTS ------------------------------------------------------------------------------------------------------------#
from template import Agent
import heapq
import math
from Sequence.sequence_model import *

class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)

    def SelectAction(self, actions, game_state):
        # usc
        action = self.uscSelectionH(actions, game_state)
        return action

    # UCS
    def uscSelectionH(self, actions, game_state):
        # avoid null action return
        nextAction = random.choice(actions)
        minScore = math.inf

        # go through current actions
        for action in actions:
            # get the "cost" if doing this action
            score = self.uscActionsH(action, game_state)
            if minScore > score:
                # keep the cost minimizing
                minScore = score
                nextAction = action

        # calculate this play cards' draft cards
        playCard = nextAction["play_card"]
        print("playCard: ",playCard)
        playPos = nextAction["coords"]

        # got the smallest distance of current possible play_card
        # then find the best draft_card using the same method
        if playCard != "jc" or playCard != "js" or playCard != "jh" or playCard != "jd":
            mindraft = math.inf
            for action in actions:
                # if it's the trade card, need to find which draft card is best
                # separately handle this is because trade has None value
                if action["type"] == "trade":
                    if action["play_card"] != None:
                        draftscore = self.uscPosH(action["draft_card"], game_state)
                        if mindraft > draftscore:
                            mindraft = draftscore
                            nextAction = action

                if action["play_card"] == playCard and action["coords"] == playPos:
                    draftscore = self.uscPosH(action["draft_card"], game_state)
                    if mindraft > draftscore:
                        mindraft = draftscore
                        nextAction = action

        return nextAction

    #  (for draft card) mini distance between one of the possible action and the goal
    def uscPosH(self, draftCard, game_state):
        # if it's jack, we take it immediately
        if draftCard == "js" or draftCard == "jh" or draftCard == "jc" or draftCard == "jd":
            return -math.inf

        points = COORDS[draftCard]

        point1s = []
        minDistance = math.inf
        temp = math.inf

        awesomeSet = set()
        awesomeSet.update(((4, 4), (4, 5), (5, 4), (5, 5), (0, 0), (0, 9), (9, 9), (9, 0)))

        # if the agent one before it has no last action, means it is the first one
        # then we need to find the closest distance between 4 hearts/4 corner with
        # all the possible actions
        if game_state.agents[(self.id - 1) % 4].last_action == None:
            point1s = list(awesomeSet)
            for point in points:
                temp = min(self.chipDistanceH(point, point1s, game_state), temp)
                minDistance = min(temp, minDistance)
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
            for point in points:
                temp = min(self.chipDistanceH(point, point1s, game_state), temp)
                minDistance = min(temp, minDistance)
            return minDistance

    #  mini distance between one of the possible action and the goal
    def uscActionsH(self, action, game_state):

        if action["type"] == "trade":
            # if got a card trade need to play it asap
            return -math.inf

        playCard = action["play_card"]

        # TODO: it's not good enough to hold it util opp occupy the 4 hearts
        # one eyed take opp from 4 hearts, two-eyed doesn't need to be considered
        # since every action will be take into consider
        if playCard == "js" or playCard == "jh":
            if action["coords"] == (4, 5) or action["coords"] == (4, 4) or \
                    action["coords"] == (5, 4) or action["coords"] == (5, 5):
                return -math.inf
            else:
                return math.inf

        point = action["coords"]

        point1s = []
        minDistance = math.inf

        # the 4 hearts and four corner
        awesomeSet = set()
        awesomeSet.update(((4, 4), (4, 5), (5, 4), (5, 5), (0, 0), (0, 9), (9, 9), (9, 0)))

        # if the agent one before it has no last action, means it is the first one
        # then we need to find the closest distance between 4 hearts/4 corner with
        # all the possible actions
        if game_state.agents[(self.id - 1) % 4].last_action == None:
            point1s = list(awesomeSet)
            minDistance = min(self.chipDistanceH(point, point1s, game_state), minDistance)
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
            minDistance = min(self.chipDistanceH(point, point1s, game_state), minDistance)
            return minDistance

    # the minimum distance between point and one of the point in point1s
    def chipDistanceH(self, point, point1s, game_state):
        # if current point is at empty four heart, play it immediately!
        if point in [(4,4),(4,5),(5,4),(5,5)]:
            if game_state.board.chips[point[0]][point[1]] == EMPTY:
                return -math.inf

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
                # if it's the first time to explore, then 8 positions around it
                # should be expanded
                if expandTime == 1:
                    succNodes = self.expandH(parent, pos, game_state, True)
                else:
                    # if not, only need to expand in one direction
                    succNodes = self.expandH(parent, pos, game_state, False)
                if succNodes == []:
                    return math.inf
                for succNode in succNodes:
                    succParent, succPos, succCost = succNode
                    newNode = (succParent, succPos, cost + succCost)
                    myqueue.push(newNode, cost + succCost)
        return totalCost

    # used to expand the node
    def expandH(self, parentPoint, point, game_state, isRoot):
        # cost of every path
        OPP = 4
        OPP_SEQ = 5
        NORMAL = 2
        AWE = 0

        # chips is used to find it expand position contains opponent
        chips = game_state.board.chips
        opp_color = game_state.agents[self.id].opp_colour
        opp_seq_color = game_state.agents[self.id].opp_seq_colour

        # point's parent
        x0, y0 = parentPoint
        # current node which is going to be expanded
        x, y = point

        # the 4 hearts and four corner
        awesomeSet = set()
        awesomeSet.update(((4, 4), (4, 5), (5, 4), (5, 5), (0, 0), (0, 9), (9, 9), (9, 0)))

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
                            # if opp is in the way, increase the cost
                            if chips[x + dx][y + dy] == opp_color:
                                children.append((point, (x + dx, y + dy), OPP))
                            elif chips[x + dx][y + dy] == opp_seq_color:
                                children.append((point, (x + dx, y + dy), OPP_SEQ))
                            # if aswesome set we want get closer, so reduce the cost
                            elif chips[x + dx][y + dy] == EMPTY and (x+dx,y+dy) in awesomeSet:
                                children.append((point, (x + dx, y + dy), AWE))
                            else:
                                children.append((point, (x + dx, y + dy), NORMAL))
        else:
            # only expand one direction
            children = []
            dx = x - x0
            dy = y - y0
            if x + dx >= 0 and x + dx < 10 and y + dy >= 0 and y + dy < 10:
                # if opp is in the way, increase the cost
                if chips[x + dx][y + dy] == opp_color:
                    children.append((point, (x + dx, y + dy), OPP))
                elif chips[x + dx][y + dy] == opp_seq_color:
                    children.append((point, (x + dx, y + dy), OPP_SEQ))
                # if aswesome set we want get closer, so reduce the cost
                elif chips[x + dx][y + dy] == EMPTY and (x + dx, y + dy) in awesomeSet:
                    children.append((point, (x + dx, y + dy), AWE))
                else:
                    children.append((point, (x + dx, y + dy), NORMAL))
        return children

# Helper Class ----------------------------------------------------------------------------#
class PriorityQueue:
    """
      Implements a priority queue data structure.
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
