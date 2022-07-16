# INFORMATION ------------------------------------------------------------------------------------------------------- #

# Author:  Steven Spratley, extending code by Guang Ho and Michelle Blom
# Date:    04/01/2021
# Purpose: Implements "Sequence" for the COMP90054 competitive game environment

# IMPORTS ------------------------------------------------------------------------------------------------------------#

import random
from Sequence.sequence_utils import *
from template import GameState, GameRule
from collections import defaultdict

# CONSTANTS ----------------------------------------------------------------------------------------------------------#

BOARD = [['jk','2s','3s','4s','5s','6s','7s','8s','9s','jk'],
         ['6c','5c','4c','3c','2c','ah','kh','qh','th','ts'],
         ['7c','as','2d','3d','4d','5d','6d','7d','9h','qs'],
         ['8c','ks','6c','5c','4c','3c','2c','8d','8h','ks'],
         ['9c','qs','7c','6h','5h','4h','ah','9d','7h','as'],
         ['tc','ts','8c','7h','2h','3h','kh','td','6h','2d'],
         ['qc','9s','9c','8h','9h','th','qh','qd','5h','3d'],
         ['kc','8s','tc','qc','kc','ac','ad','kd','4h','4d'],
         ['ac','7s','6s','5s','4s','3s','2s','2h','3h','5d'],
         ['jk','ad','kd','qd','td','9d','8d','7d','6d','jk']]

#Store dict of cards and their coordinates for fast lookup.
COORDS = defaultdict(list)
for row in range(10):
    for col in range(10):
        COORDS[BOARD[row][col]].append((row,col))
        
# CLASS DEF ----------------------------------------------------------------------------------------------------------#       

#Represents game as a deck, board (with chips), and agents.
class SequenceState(GameState):
    class Deck:
        def __init__(self):
            self.cards = self.new_deck()
            self.discards = []
            
        def new_deck(self):
            cards = [(r+s) for r in ['2','3','4','5','6','7','8','9','t','j','q','k','a'] for s in ['d','c','h','s']]
            cards = cards*2 #Sequence uses 2 decks.
            random.shuffle(cards)
            return cards
            
        def deal(self, num_cards=1):
            hand = []
            random.shuffle(self.cards)
            for _ in range(num_cards):
                try:
                    hand.append(self.cards.pop())
                except IndexError: #Deck is empty.
                    break
            return hand
            
    class BoardState:
        def __init__(self):
            self.new_seq = False
            self.chips = [[EMPTY for _ in range(10)] for _ in range(10)]
            self.draft = []
            self.plr_coords = {RED:[], BLU:[]}
            self.empty_coords = [(r,c) for r in range(10) for c in range(10) if (r,c) not in COORDS['jk']]
            for r,c in COORDS['jk']:
                self.chips[r][c] = JOKER
            
    class AgentState:
        def __init__(self, _id):
            self.id = _id
            self.agent_trace = AgentTrace(_id)
            self.colour         = BLU     if _id%2 else RED
            self.opp_colour     = RED     if _id%2 else BLU
            self.seq_colour     = BLU_SEQ if _id%2 else RED_SEQ
            self.opp_seq_colour = RED_SEQ if _id%2 else BLU_SEQ
            self.completed_seqs = 0
            self.score = 0 #Currently, score and completed_seqs are the same in this game. Leaving in for possibility of extension.
            self.seq_orientations = []
            self.hand = None
            self.discard = None
            self.trade = False
            self.last_action = None

    def __init__(self, num_agents):
        self.deck = self.Deck()
        self.board = self.BoardState()
        self.agents = []
        #Deal draft cards.
        self.board.draft = self.deck.deal(5)
        #Deal agent hands.
        for i in range(num_agents):
            ps = self.AgentState(i)
            ps.hand = self.deck.deal(6)
            self.agents.append(ps)


#Implements game logic.
class SequenceGameRule(GameRule):
    def __init__(self,num_of_agent):
        super().__init__(num_of_agent)
        self.private_information = ["hand"] #Private information is a list of agent attributes that cannot be known between agents.

    def initialGameState(self):
        return SequenceState(self.num_of_agent)
    
    #Returns a list of sequence coordinates if a sequence has just been formed. Else, returns None.
    def checkSeq(self, chips, plr_state, last_coords):
        clr,sclr   = plr_state.colour, plr_state.seq_colour
        oc,os      = plr_state.opp_colour, plr_state.opp_seq_colour
        seq_type   = TRADSEQ
        seq_coords = []
        seq_found  = {'vr':0, 'hz':0, 'd1':0, 'd2':0, 'hb':0}
        found      = False
        nine_chip  = lambda x,clr : len(x)==9 and len(set(x))==1 and clr in x
        lr,lc      = last_coords
        
        #All joker spaces become player chips for the purposes of sequence checking.
        for r,c in COORDS['jk']:
            chips[r][c] = clr
        
        #First, check "heart of the board" (2h, 3h, 4h, 5h). If possessed by one team, the game is over.
        coord_list = [(4,4),(4,5),(5,4),(5,5)]
        heart_chips = [chips[y][x] for x,y in coord_list]
        if EMPTY not in heart_chips and (clr in heart_chips or sclr in heart_chips) and not (oc in heart_chips or os in heart_chips):
            seq_type = HOTBSEQ
            seq_found['hb']+=2
            seq_coords.append(coord_list)
            
        #Search vertical, horizontal, and both diagonals.
        vr = [(-4,0),(-3,0),(-2,0),(-1,0),(0,0),(1,0),(2,0),(3,0),(4,0)]
        hz = [(0,-4),(0,-3),(0,-2),(0,-1),(0,0),(0,1),(0,2),(0,3),(0,4)]
        d1 = [(-4,-4),(-3,-3),(-2,-2),(-1,-1),(0,0),(1,1),(2,2),(3,3),(4,4)]
        d2 = [(-4,4),(-3,3),(-2,2),(-1,1),(0,0),(1,-1),(2,-2),(3,-3),(4,-4)]
        for seq,seq_name in [(vr,'vr'), (hz,'hz'), (d1,'d1'), (d2,'d2')]:
            coord_list = [(r+lr, c+lc) for r,c in seq]
            coord_list = [i for i in coord_list if 0<=min(i) and 9>=max(i)] #Sequences must stay on the board.
            chip_str   = ''.join([chips[r][c] for r,c in coord_list])
            #Check if there exists 4 player chips either side of new chip (counts as forming 2 sequences).
            if nine_chip(chip_str, clr):
                seq_found[seq_name]+=2
                seq_coords.append(coord_list)
            #If this potential sequence doesn't overlap an established sequence, do fast check.
            if sclr not in chip_str:
                sequence_len = 0
                start_idx    = 0
                for i in range(len(chip_str)):
                    if chip_str[i] == clr:
                        sequence_len += 1
                    else:
                        start_idx = i+1
                        sequence_len = 0
                    if sequence_len >= 5:
                        seq_found[seq_name] += 1
                        seq_coords.append(coord_list[start_idx:start_idx+5])    
                        break
            else: #Check for sequences of 5 player chips, with a max. 1 chip from an existing sequence.
                for pattern in [clr*5, clr*4+sclr, clr*3+sclr+clr, clr*2+sclr+clr*2, clr+sclr+clr*3, sclr+clr*4]:
                    for start_idx in range(5):
                        if chip_str[start_idx:start_idx+5] == pattern:
                            seq_found[seq_name]+=1
                            seq_coords.append(coord_list[start_idx:start_idx+5])
                            found = True
                            break
                    if found:
                        break
        
        for r,c in COORDS['jk']:
            chips[r][c] = JOKER #Joker spaces reset after sequence checking.
        
        num_seq = sum(seq_found.values())
        if num_seq > 1 and seq_type != HOTBSEQ:
            seq_type = MULTSEQ
        return ({'num_seq':num_seq, 'orientation':[k for k,v in seq_found.items() if v], 'coords':seq_coords}, seq_type) if num_seq else (None,None)

    def generateSuccessor(self, state, action, agent_id):
        state.board.new_seq = False
        print(f"agent id {agent_id}")
        plr_state = state.agents[agent_id]
        plr_state.last_action = action #Record last action such that other agents can make use of this information.
        reward = 0
                
        #Update agent state. Take the card in play from the agent, discard, draw the selected draft, deal a new draft.
        #If agent was allowed to trade but chose not to, there is no card played, and hand remains the same.
        card  = action['play_card']
        draft = action['draft_card']
        if card:
            plr_state.hand.remove(card)                 #Remove card from hand.
            plr_state.discard = card                    #Add card to discard pile.
            state.deck.discards.append(card)            #Add card to global list of discards (some agents might find tracking this helpful).
            state.board.draft.remove(draft)             #Remove draft from draft selection.
            plr_state.hand.append(draft)                #Add draft to player hand.
            state.board.draft.extend(state.deck.deal()) #Replenish draft selection.
        
        #If action was to trade in a dead card, action is complete, and agent gets to play another card.
        if action['type']=='trade':
            plr_state.trade = True #Switch trade flag to prohibit agent performing a second trade this turn.
            return state

        #Update Sequence board. If action was to place/remove a marker, add/subtract it from the board.
        r,c = action['coords']
        if action['type']=='place':
            state.board.chips[r][c] = plr_state.colour
            state.board.empty_coords.remove(action['coords'])
            state.board.plr_coords[plr_state.colour].append(action['coords'])            
        elif action['type']=='remove':
            state.board.chips[r][c] = EMPTY
            state.board.empty_coords.append(action['coords'])
        else:
            print("Action unrecognised.")
        
        #Check if a sequence has just been completed. If so, upgrade chips to special sequence chips.
        if action['type']=='place':
            seq,seq_type = self.checkSeq(state.board.chips, plr_state, (r,c))
            if seq:
                reward += seq['num_seq']
                state.board.new_seq = seq_type
                for sequence in seq['coords']:
                    for r,c in sequence:
                        if state.board.chips[r][c] != JOKER: #Joker spaces stay jokers.
                            state.board.chips[r][c] = plr_state.seq_colour
                            try:
                                state.board.plr_coords[plr_state.colour].remove(action['coords'])
                            except: #Chip coords were already removed with the first sequence.
                                pass
                plr_state.completed_seqs += seq['num_seq']
                plr_state.seq_orientations.extend(seq['orientation'])
        
        plr_state.trade = False #Reset trade flag if agent has completed a full turn.
        plr_state.agent_trace.action_reward.append((action,reward)) #Log this turn's action and any resultant score.
        plr_state.score += reward
        return state
    
    
    #Changes update() from template.py by keeping the current agent in play after trading a dead card.
    def update(self, action):
        temp_state = self.current_game_state
        self.current_game_state = self.generateSuccessor(temp_state, action, self.current_agent_index)
        #If current action is to trade, agent in play continues their turn.
        self.current_agent_index = self.getNextAgentIndex() if action['type']!='trade' else self.current_agent_index
        self.action_counter += 1


    def gameEnds(self): #Game ends if a team has formed at least 2 sequences, or if the deck is empty.
        scores = {RED:0, BLU:0}
        for plr_state in self.current_game_state.agents:
            scores[plr_state.colour] += plr_state.completed_seqs
        return scores[RED]>=2 or scores[BLU]>=2 or len(self.current_game_state.board.draft)==0


    def calScore(self, game_state,agent_id):
        return game_state.agents[agent_id].completed_seqs


    def getLegalActions(self, game_state, agent_id):
        actions = []
        agent_state = game_state.agents[agent_id]
        
        #First, give the agent the option to trade a dead card, if they haven't just done so.
        if not agent_state.trade:
            for card in agent_state.hand:
                if card[0]!='j':
                    free_spaces = 0
                    for r,c in COORDS[card]:
                        if game_state.board.chips[r][c]==EMPTY:
                            free_spaces+=1
                    if not free_spaces: #No option to place, so card is considered dead and can be traded.
                        for draft in game_state.board.draft:
                            actions.append({'play_card':card, 'draft_card':draft, 'type':'trade', 'coords':None})
                        
            if len(actions): #If trade actions available, return those, along with the option to forego the trade.
                actions.append({'play_card':None, 'draft_card':None, 'type':'trade', 'coords':None})
                return actions
                
        #If trade is prohibited, or no trades available, add action/s for each card in player's hand.
        #For each action, add copies corresponding to the various draft cards that could be selected at end of turn.
        for card in agent_state.hand:
            if card in ['jd','jc']: #two-eyed jacks
                for r in range(10):
                    for c in range(10):
                        if game_state.board.chips[r][c]==EMPTY:
                            for draft in game_state.board.draft:
                                actions.append({'play_card':card, 'draft_card':draft, 'type':'place', 'coords':(r,c)})
                            
            elif card in ['jh','js']: #one-eyed jacks
                for r in range(10):
                    for c in range(10):
                        if game_state.board.chips[r][c]==agent_state.opp_colour:
                            for draft in game_state.board.draft:
                                actions.append({'play_card':card, 'draft_card':draft, 'type':'remove', 'coords':(r,c)})
            
            else: #regular cards
                for r,c in COORDS[card]:
                    if game_state.board.chips[r][c]==EMPTY:
                        for draft in game_state.board.draft:
                            actions.append({'play_card':card, 'draft_card':draft, 'type':'place', 'coords':(r,c)})
                    
        return actions

# END FILE -----------------------------------------------------------------------------------------------------------#