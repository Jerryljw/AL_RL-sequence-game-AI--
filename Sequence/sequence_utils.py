# INFORMATION ------------------------------------------------------------------------------------------------------- #

# Author:  Steven Spratley, extending code by Guang Ho and Michelle Blom
# Date:    04/01/2021
# Purpose: Implements "Sequence" for the COMP90054 competitive game environment

# CLASS DEF ----------------------------------------------------------------------------------------------------------#

RED     = 'r'
BLU     = 'b'
RED_SEQ = 'X'
BLU_SEQ = 'O'
JOKER   = '#'
EMPTY   = '_'
TRADSEQ = 1
HOTBSEQ = 2
MULTSEQ = 3

# Bundle together an agent's activity in the game for use in updating a policy.
class AgentTrace:
    def __init__(self, pid):
        self.id = pid
        self.action_reward = [] # Turn-by-turn history consisting of (action,reward) tuples.
    
def ActionToString(agent_id, action, new_seq):
    if action['type']=='trade':
        if action['play_card']:
            desc = "Agent #{} traded in '{}' as a dead card, selecting '{}' in exchange."\
                .format(agent_id, action['play_card'], action['draft_card'])
        else:
            desc = 'Agent #{} decided to keep a dead card.'.format(agent_id)
    elif action['type']=='place':
        if new_seq==TRADSEQ:
            desc = "Agent #{} played '{}' to place a marker on space {}, forming a new sequence!".format(agent_id, action['play_card'], action['coords'])
        elif new_seq==HOTBSEQ:
            desc = "Agent #{} played '{}' to place a marker on space {}, gaining \"Heart of the Board!\"".format(agent_id, action['play_card'], action['coords'])
        elif new_seq==MULTSEQ:
            desc = "Agent #{} played '{}' to place a marker on space {}, forming multiple sequences!".format(agent_id, action['play_card'], action['coords'])
        else:
            desc = "Agent #{} played '{}' to place a marker on space {}.".format(agent_id, action['play_card'], action['coords'])
    elif action['type']=='remove':
        desc = "Agent #{} played '{}' to remove a marker from space {}.".format(agent_id, action['play_card'], action['coords'])
    return desc

def AgentToString(agent_id, ps):
    desc = "Agent #{}, playing for team {}, is holding cards {}.\n".format(agent_id, ps.colour.capitalize(), ps.hand)
    return desc

def BoardToString(game_state):
    c = game_state.board.chips
    desc = "{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n"\
        .format(c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],c[8],c[9])
    return desc

# END FILE -----------------------------------------------------------------------------------------------------------#