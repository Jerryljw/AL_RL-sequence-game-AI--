# INFORMATION ------------------------------------------------------------------------------------------------------- #

# Author:  Jiawei Luo, Yifan Deng, Xinzhe Wang
# Date:    05/19/2021
# Purpose: Implementing Heuristic Search in agent of the Sequence Game

# IMPORTS ------------------------------------------------------------------------------------------------------------#
from template import Agent
from Sequence.sequence_model import BOARD, COORDS
from Sequence.sequence_utils import JOKER

# CONSTANTS ----------------------------------------------------------------------------------------------------------#

# Default heuristic values.
HEURISTIC = [[100,3,4,4,4,4,4,4,3,100],
             [3,4,4,4,4,4,4,4,4,3],
             [4,4,4,4,4,4,4,4,4,4],
             [4,4,4,4,4,4,4,4,4,4],
             [4,4,4,4,0,0,4,4,4,4],
             [4,4,4,4,0,0,4,4,4,4],
             [4,4,4,4,4,4,4,4,4,4],
             [4,4,4,4,4,4,4,4,4,4],
             [3,4,4,4,4,4,4,4,4,3],
             [100,3,4,4,4,4,4,4,3,100]]

# Weighted value.
# If the ATTACK > DEFENSE, we pay more attention to form our sequence.
# otherwise, we pay more attention to stop the enemy from forming sequence.
ATTACK = 1
DEFENSE = 0.1

# CLASS DEF ----------------------------------------------------------------------------------------------------------#
class myAgent(Agent):
    def __init__(self, _id):
        super().__init__(_id)

    # This method is used to calculate the heuristic value for each position on the board
    def GetChipsHeuristic(self, colour, seq_us_colour, seq_opp_colour, chips):
        temp = [(i, j) for i in range(10) for j in range(10)]
        # delete special coords whose h-value is fixed.
        temp.remove((0, 0))
        temp.remove((0, 9))
        temp.remove((9, 0))
        temp.remove((9, 9))
        temp.remove((4, 4))
        temp.remove((4, 5))
        temp.remove((5, 4))
        temp.remove((5, 5))

        for (i,j) in temp:
            # For chips that cannot be changed, it is not necessary to generate their h-values
            if chips[i][j] == colour or chips[i][j] == seq_us_colour or chips[i][j] == seq_opp_colour:
                temp.remove((i,j))

        chipsHeuristic = HEURISTIC
        for pair in temp:
            i,j = pair
            hori = 0
            vert = 0
            diag = 0
            cdia = 0
            for di in range(1,5):
                if i-di >= 0:
                    if chips[i - di][j] == JOKER or chips[i - di][j] == colour:
                        hori = hori + 1
                else:
                    break
            for di in range(1,5):
                if i+di <= 9:
                    if chips[i + di][j] == JOKER or chips[i + di][j] == colour:
                        hori = hori + 1
                else:
                    break
            for di in range(1,5):
                if j-di >= 0:
                    if chips[i][j - di] == JOKER or chips[i][j - di] == colour:
                        vert = vert + 1
                else:
                    break
            for di in range(1,5):
                if j+di < 10:
                    if chips[i][j + di] == JOKER or chips[i][j + di] == colour:
                        vert = vert + 1
                else:
                    break
            for di in range(1,5):
                if i-di >= 0 and j-di >= 0:
                    if chips[i - di][j - di] == JOKER or chips[i - di][j - di] == colour:
                        diag = diag + 1
                else:
                    break
            for di in range(1,5):
                if i+di <= 9 and j+di <= 9:
                    if chips[i + di][j + di] == JOKER or chips[i + di][j + di] == colour:
                        diag = diag + 1
                else:
                    break
            for di in range(1,5):
                if i+di <= 9 and j-di >= 0:
                    if chips[i + di][j - di] == JOKER or chips[i + di][j - di] == colour:
                        cdia = cdia + 1
                else:
                    break
            for di in range(1,5):
                if i-di >= 0 and j+di <= 9:
                    if chips[i - di][j + di] == JOKER or chips[i - di][j + di] == colour:
                       cdia = cdia + 1
                else:
                   break
            max_seq = max(hori,vert,diag,cdia)
            hvalue = max(4-max_seq, 0)
            chipsHeuristic[i][j] = hvalue

        return chipsHeuristic

    def GetCardHeuristic(self, chipsHeuristic):
        cards = [(r + s) for r in ['2', '3', '4', '5', '6', '7', '8', '9', 't', 'q', 'k', 'a'] for s in
                 ['d', 'c', 'h', 's']]
        cardsHeuristic = {i: 10000 for i in cards}
        cardsHeuristic["jd"] = 0
        cardsHeuristic["jc"] = 0
        cardsHeuristic["jh"] = 0
        cardsHeuristic["js"] = 0

        for card in cards:
            positions = COORDS[card]
            sumValue = 0
            for position in positions:
                x,y = position
                sumValue += chipsHeuristic[x][y]
            cardsHeuristic[card] = sumValue / len(positions)

        return cardsHeuristic

    def SelectAction(self, actions, game_state):
        attackH = self.GetChipsHeuristic(game_state.agents[self.id].colour, game_state.agents[self.id].seq_colour,
                                        game_state.agents[self.id].opp_seq_colour, game_state.board.chips)
        defenseH = self.GetChipsHeuristic(game_state.agents[self.id].opp_colour, game_state.agents[self.id].opp_seq_colour,
                                        game_state.agents[self.id].seq_colour, game_state.board.chips)
        chipsH = []
        for i in range(len(attackH)):
            temp = []
            for j in range(len(attackH[i])):
                temp.append(ATTACK * attackH[i][j] + DEFENSE * defenseH[i][j])
            chipsH.append(temp)

        cardsH = self.GetCardHeuristic(chipsH)

        if actions[0]["type"] == 'trade':
            actionsList = []
            for action in actions:
                if action["draft_card"] is not None:
                    actionsList.append((cardsH[action["draft_card"]], action))
            actionsList.sort(key=lambda k:k[0])
            return actionsList[0][1]

        else:
            actionsList = []
            for action in actions:
                x, y = action["coords"]
                actionsList.append((cardsH[action["draft_card"]] + chipsH[x][y], action))
            actionsList.sort(key=lambda k:k[0])
            return actionsList[0][1]
