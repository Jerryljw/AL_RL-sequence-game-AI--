# INFORMATION ------------------------------------------------------------------------------------------------------- #

# Author:  Jiawei Luo, Yifan Deng, Xinzhe Wang
# Date:    05/19/2021
# Purpose: Implementing MCTS with UCB in agent of the Sequence Game

# IMPORTS ------------------------------------------------------------------------------------------------------------#
import copy
import math
import time

from template import Agent
import random
from Sequence.sequence_model import BOARD, COORDS
from Sequence.sequence_utils import *


class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)

    def SelectAction(self, actions, game_state):
        trade = False
        for action in actions:
            if action['type'] == 'trade':
                trade = True
                break
        if trade:
            return random.choice(actions)
        else:
            timeleft = 0.9 # the time limit each round
            color = game_state.agents[self.id].colour
            thisMcts = MCTS(actions, game_state, color)
            root_Node = thisMcts.mcts(timeleft)
            bestChild = root_Node.findBest_child()
            choice_action = bestChild._last_action
            return choice_action


class Node:
    def __init__(self, game_state, drafts, actions, player_color, discountFactor = 0.9,last_action=None, parent=None):
        self._game_state = game_state
        self._drafts = drafts
        self._actions = actions
        self._player_color = player_color
        self._discountFactor = discountFactor
        self._parent = parent
        self._last_action = last_action
        # initial visits to 1, avoid divide by zero
        self._children = []
        self._visits = 1
        self._value_Q = 0.0
    """
    return the q value of this node
    """
    def getValue(self):
        return self._value_Q

    """
    if not expanded, expand and return random child,
    if expanded, return least visited child
    """
    def select(self):
        if len(self._children) == 0:
            self.expand()
            return random.choice(self._children)
        else:
            least_nodes = self._children[0]
            for child in self._children:
                if child._visits < least_nodes._visits:
                    least_nodes = child
            # least_nodes = least_nodes.select()
            return least_nodes
    """
    add all children
    """
    def expand(self):
        current_game_state = copy.deepcopy(self._game_state)
        current_player_color = self._player_color
        current_actions = copy.deepcopy(self._actions)
        current_drafts = copy.deepcopy(self._drafts)
        if len(current_drafts) > 0:
            limit = 0
            for action in current_actions:
                if limit > 40:
                    break
                newState, newActions, newDraft = generateNextState(current_game_state, action, current_actions,
                                                                   current_drafts, current_player_color)
                self._children.append(
                    Node(newState, newDraft, newActions, current_player_color, last_action=action, parent=self))
                limit += 1
    """
    backPropagation
    """
    def backPropagate(self, reward):
        self._visits += 1
        self._value_Q = self._value_Q + reward
        if self._parent is None:
            return
        self._parent.backPropagate(reward*self._discountFactor)
    """
    node that reach end state
    """
    def endState(self):
        return len(self._drafts) <= 0
    """
    return child with largest q value
    """
    def findBest_child(self):
        bestChild = self._children[0]
        for child in self._children:
            if child.calcuate_UCB() > bestChild.calcuate_UCB():
                bestChild = child
        return bestChild

    def calcuate_UCB(self):
        C_p = 1/math.sqrt(2.0)
        # UCB = q_value / visits + 2C_p * sqrt(2 * ln(total_visits) / visits)
        total_visits = self._parent._visits
        visits = self._visits
        Q_s_a = self._value_Q
        usb = Q_s_a / visits + 2* C_p * math.sqrt(2 * math.log(total_visits)/visits)
        return usb




class MCTS(object):
    def __init__(self, actions, game_state, player_color, discountFactor=0.9, maxDepth=6):
        self._actions = actions
        self._game_state = game_state
        self._player_color = player_color
        self._discountFactor = discountFactor
        self._maxDepth = maxDepth

    def mcts(self, timeout=0.9):
        current_drafts = copy.deepcopy(self._game_state.board.draft)
        current_chips_board = copy.deepcopy(self._game_state.board.chips)
        current_actions = copy.deepcopy(self._actions)
        current_player_color = copy.deepcopy(self._player_color)

        # defind root_Node
        root_Node = Node(current_chips_board, current_drafts, current_actions, current_player_color, last_action=None,
                         parent=None)
        # record the start time
        start_time = int(time.time() * 1000)
        current_time = int(time.time() * 1000)
        while current_time < start_time + timeout * 1000 and len(root_Node._actions)>0 and len(root_Node._drafts)>0:
            # select least visited sub node in root_Node's children, expand it if it is not expended
            selected_Node = root_Node.select()
            reward = 0
            root_state = copy.deepcopy(current_chips_board)
            selected_Node_last_action = copy.deepcopy(selected_Node._last_action)
            reward = calReward(selected_Node_last_action, root_state, self._player_color)
            if current_time > start_time + timeout * 1000:
                break
            # if selected_Node is not backPropagated, simulate it and do backPropagate
            reward += self.simulate(selected_Node)
            if current_time > start_time + timeout * 1000:
                break
            selected_Node.backPropagate(reward)
            current_time = int(time.time() * 1000)

        return root_Node
    """
    simulation of selected node
    """
    def simulate(self, node):
        node_copy = copy.deepcopy(node)
        current_game_state = copy.deepcopy(node._game_state)
        actions_copy = copy.deepcopy(node._actions)
        drafts_copy = copy.deepcopy(node._drafts)
        cumulativeReward = 0.0
        depth = 1
        # do simulate while there are actions and drafts
        while (depth < self._maxDepth) and len(drafts_copy) > 0 and len(actions_copy) > 0:
            # randomly choose actions
            this_color = self._player_color
            this_seq_color = 'X'
            if this_color == 'b':
                this_seq_color = 'O'
            reward = 0.0
            if len(drafts_copy) > 0:
                # action_copy, rewardMax = maxRewareAction(actions_copy, current_game_state, this_color)
                action_copy = random.choice(actions_copy) # randomly choose action
                rewardMax = calReward(action_copy, current_game_state, this_color)
                newState, actions_copy, drafts = generateNextState(current_game_state, action_copy, actions_copy,
                                                                   drafts_copy, this_color)
                reward += rewardMax
                current_game_state = newState
            cumulativeReward += pow(self._discountFactor, depth) * reward
            depth += 1
        return cumulativeReward/depth

"""
select the largest reward action
"""
def maxRewareAction(current_actions, current_game_state, color):
    best_action = current_actions[0]
    maxReward = calReward(best_action, current_game_state, color)
    for current_action in current_actions:
        tempReward = calReward(current_action, current_game_state, color)
        if maxReward < tempReward:
            maxReward = tempReward
            best_action = current_action
    return best_action, maxReward

"""
calculate the reward based on action, current game board chips and color
"""
def calReward(this_action, this_game_state, this_color):
    better_cards = ['jd', 'jc', 'jh', 'js']
    best_cards = ['5h', '4h', '2h', '3h']
    best_coords = [(4, 4), (4, 5), (5, 4), (5, 5)]
    seqs = [[(-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
            [(0, -4), (0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4)],
            [(-4, -4), (-3, -3), (-2, -2), (-1, -1), (0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],
            [(-4, 4), (-3, 3), (-2, 2), (-1, 1), (0, 0), (1, -1), (2, -2), (3, -3), (4, -4)]]
    opp_colour = 'r'
    opp_seq_colour = 'X'
    seq_colour = 'O'
    if this_color == 'r':
        opp_colour = 'b'
        opp_seq_colour = 'O'
        seq_colour = 'X'

    x, y = this_action['coords']
    max_place_length = 0

    if this_action['type'] == 'place':
        for seq in seqs:
            window_length = 5
            for i in range(len(seq) - window_length + 1):
                window = []
                dx, dy = seq[i]
                for j in range(window_length):
                    if x + dx + j >= 0 and y + dy + j >= 0 and x + dx + j < 10 and y + dy + j < 10:
                        if this_game_state[x + dx + j][y + dy + j] == this_color or this_game_state[x + dx + j][
                            y + dy + j] == '#' or this_game_state[x + dx + j][y + dy + j] == seq_colour:
                            window.append(1)
                        elif this_game_state[x + dx + j][y + dy + j] == opp_colour or this_game_state[x + dx + j][
                            y + dy + j] == opp_seq_colour:
                            window.append(-1)
                        else:
                            window.append(0)
                if max_place_length < abs(sum(window)):
                    max_place_length = abs(sum(window))
    elif this_action['type'] == 'remove':
        for seq in seqs:
            window_length = 5
            for i in range(len(seq) - window_length + 1):
                window = []
                dx, dy = seq[i]
                for j in range(window_length):
                    if x + dx + j >= 0 and y + dy + j >= 0 and x + dx + j < 10 and y + dy + j < 10:
                        if this_game_state[x + dx + j][y + dy + j] == opp_colour or this_game_state[x + dx + j][
                            y + dy + j] == opp_seq_colour:
                            window.append(-1)
                        else:
                            window.append(0)
                if max_place_length < abs(sum(window)):
                    max_place_length = abs(sum(window))
    max_draft_place_length = 0
    if this_action['draft_card'] not in ['jd', 'jc', 'jh', 'js']:
        draft_coords = COORDS[this_action['draft_card']]
        for coords in draft_coords:
            x1, y1 = coords
            for seq in seqs:
                window_length = 5
                for i in range(len(seq) - window_length + 1):
                    window = []
                    dx, dy = seq[i]
                    for j in range(window_length):
                        if x1 + dx + j >= 0 and y1 + dy + j >= 0 and x1 + dx + j < 10 and y1 + dy + j < 10:
                            if this_game_state[x1 + dx + j][y1 + dy + j] == this_color or this_game_state[x1 + dx + j][
                                y1 + dy + j] == '#' or this_game_state[x1 + dx + j][y1 + dy + j] == seq_colour:
                                window.append(1)
                            elif this_game_state[x1 + dx + j][y1 + dy + j] == opp_colour or \
                                    this_game_state[x1 + dx + j][
                                        y1 + dy + j] == opp_seq_colour:
                                window.append(-1)
                            else:
                                window.append(0)
                    if max_draft_place_length < abs(sum(window)):
                        max_draft_place_length = abs(sum(window))
    reward = 0.0
    reward += max_place_length if this_action['type'] == 'remove' else max_place_length * 2
    reward += max_draft_place_length
    if max_draft_place_length == 4:
        reward += 10000
    if max_place_length == 4 or max_place_length == 5:
        reward += 999999
    if this_action['draft_card'] in better_cards:
        reward += 100
    elif this_action['draft_card'] in best_cards:
        reward += 999999
    if this_action['coords'] in best_coords:
        reward += 999999
    elif this_action['play_card'] in better_cards:
        reward += 100
    return reward

"""
get the next board chips, next actions and drafts by action
"""
def generateNextState(gameChips, action, actions, drafts, colour):
    gameChips_copy = copy.deepcopy(gameChips)
    actions_copy = copy.deepcopy(actions)
    action_copy = copy.deepcopy(action)
    drafts_copy = copy.deepcopy(drafts)
    x, y = action_copy['coords']
    draft_card = action_copy['draft_card']
    if action_copy['type'] == 'place':
        if gameChips_copy[x][y] == EMPTY:
            gameChips_copy[x][y] = colour
    elif action_copy['type'] == 'remove':
        gameChips_copy[x][y] = EMPTY

    if len(drafts_copy) > 0 and draft_card in drafts_copy:
        drafts_copy.remove(draft_card)

    opp_colour = 'b'
    if colour == 'b':
        opp_colour = 'r'

    if len(drafts_copy) > 0:
        if draft_card in ['jd', 'jc']:  # two-eyed jacks
            for r in range(10):
                for c in range(10):
                    if gameChips_copy[r][c] == EMPTY:
                        for draft in drafts_copy:
                            actions_copy.append(
                                {'play_card': draft_card, 'draft_card': draft, 'type': 'place', 'coords': (r, c)})
        elif draft_card in ['jh', 'js']:  # one-eyed jacks
            for r in range(10):
                for c in range(10):
                    if gameChips_copy[r][c] == opp_colour:
                        for draft in drafts_copy:
                            actions_copy.append(
                                {'play_card': draft_card, 'draft_card': draft, 'type': 'remove', 'coords': (r, c)})
        else:  # regular cards
            for r, c in COORDS[draft_card]:
                if gameChips_copy[r][c] == EMPTY:
                    for draft in drafts_copy:
                        actions_copy.append(
                            {'play_card': draft_card, 'draft_card': draft, 'type': 'place', 'coords': (r, c)})

        for action1 in actions_copy:
            if action1['play_card'] == action_copy['play_card'] or action1['draft_card'] == action_copy['draft_card']:
                actions_copy.remove(action1)
    return gameChips_copy, actions_copy, drafts_copy
