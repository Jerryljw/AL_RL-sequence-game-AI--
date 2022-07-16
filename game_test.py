
#- args agent_list, list of agents
#- args seed, random seed used
#- args time_limit, time limit for each step, None for inf time
#- args warning_limit, timeout warnings 
#- args displayer, TextDisplayer, GUIDisplayer or None
#- args agents_namelist, name to display
#- return replay, a dict

import random
import copy
import sys
from   template import GameState

# from displayer import *
from func_timeout import func_timeout, FunctionTimedOut
import time
    
class Game:
    def __init__(self, GameRule,
                 agent_list, 
                 num_of_agent,
                 seed=1, 
                 time_limit=1, 
                 warning_limit=3, 
                 displayer = None, 
                 agents_namelist = ["Alice","Bob"]):
        
        self.seed = seed
        random.seed(self.seed)
        self.seed_list = [random.randint(0,1e10) for _ in range(1000)]
        self.seed_idx = 0

        # Make sure we are forming a valid game, and that agent
        # id's range from 0 to N-1, where N is the number of agents.
        # assert(len(agent_list) <= 4)
        # assert(len(agent_list) > 1)

        i = 0
        for plyr in agent_list:
            assert(plyr.id == i)    
            i += 1

        self.game_rule = GameRule(num_of_agent)
        self.agents = agent_list
        self.agents_namelist = agents_namelist

        self.time_limit = time_limit
        self.warning_limit = warning_limit
        self.warnings = [0]*len(agent_list)
        self.warning_positions = []

        self.displayer = displayer
        
        if self.displayer is not None:
            self.displayer.InitDisplayer(self)

    def _EndGame(self,num_of_agent,history, isTimeOut = True, id = None):
        history.update({"seed":self.seed,
                        "num_of_agent":num_of_agent,
                        "agents_namelist":self.agents_namelist,
                        "warning_positions":self.warning_positions,
                        "warning_limit":self.warning_limit})
        history["scores"]= {i:0 for i in range(num_of_agent)}
        if isTimeOut:
            history["scores"][id] = -1
        else:
            for i in range(num_of_agent):
                history["scores"].update({i:self.game_rule.calScore(self.game_rule.current_game_state,i)})

        if self.displayer is not None:
            self.displayer.EndGame(self.game_rule.current_game_state,history["scores"])
        return history

    def Run(self):
        history = {"actions":[]}
        action_counter = 0

        ## TODO: new!!!!!!!!!!!
        for i in range(len(self.agents)):
            agent = self.agents[i]
            game_state = self.game_rule.current_game_state
            actions = self.game_rule.getLegalActions(game_state, i)

            if ("register" in dir(agent)):
                agent.register((copy.deepcopy(game_state), copy.deepcopy(actions)))
        ##

        while not self.game_rule.gameEnds():
            agent_index = self.game_rule.getCurrentAgentIndex()
            agent = self.agents[agent_index]
            game_state = self.game_rule.current_game_state
            actions = self.game_rule.getLegalActions(game_state, agent_index)
            actions_copy = copy.deepcopy(actions)
            gs_copy = copy.deepcopy(game_state)

            ## TODO: new !!!
            observation =(copy.deepcopy(game_state), copy.deepcopy(actions))
            if 'observationFunction' in dir(agent):
                observation = agent.observationFunction((copy.deepcopy(game_state),
                                                         copy.deepcopy(actions)))
            ##

            # Delete all specified attributes in the agent state copies, if this isn't a perfect information game.
            if self.game_rule.private_information:
                delattr(gs_copy.deck, 'cards') # Upcoming cards cannot be observed.
                for i in range(len(gs_copy.agents)):
                    if gs_copy.agents[i].id != agent_index:
                        for attr in self.game_rule.private_information:
                            delattr(gs_copy.agents[i], attr)
            
            # Allow agent to select action within time limit. Any error will result in one warning.
            try:
                ## TODO:CHANGED!!
                ##selected = func_timeout(self.time_limit,agent.SelectAction,args=(actions_copy, gs_copy))
                selected = func_timeout(self.time_limit, agent.SelectAction, args=(actions_copy, observation[0]))
                ##

            except AttributeError:
                print("[AttributeError]: SelectAction() is not defined!")
                print("Selecting random action instead!")
                self.warnings[agent_index] += 1
                selected = random.choice(actions_copy)
                if self.displayer is not None:
                    self.displayer.TimeOutWarning(self,agent_index)
                self.warning_positions.append((agent_index,action_counter))

            except FunctionTimedOut:
                print("[TimeoutError] timeout when calling SelectAction()!")
                print("Selecting random action instead!")
                self.warnings[agent_index] += 1
                selected = random.choice(actions_copy)
                if self.displayer is not None:
                    self.displayer.TimeOutWarning(self,agent_index)
                self.warning_positions.append((agent_index,action_counter))
                
            except:
                print("[OtherError] error occured when calling SelectAction()!")
                print("Selecting random action instead!")
                self.warnings[agent_index] += 1
                selected = random.choice(actions_copy)
                if self.displayer is not None:
                    self.displayer.TimeOutWarning(self,agent_index)
                self.warning_positions.append((agent_index,action_counter))

            # None is considered as an invalid action.
            if selected is None:
                print("[Warning] action \"None\" is returned by SelectAction()!")
                print("Selecting random action instead!")
                selected = random.choice(actions_copy)
                if self.displayer is not None:
                    self.displayer.TimeOutWarning(self,agent_index)
                self.warnings[agent_index] += 1
                self.warning_positions.append((agent_index,action_counter))

            # if the agent return invalid action, we choose a random action, and add 1 warning as penalty
            # print(f"action is: {selected}")
            # print(f"list is: {actions}")
            if not selected in actions_copy:
                print(f"[Warning] invalid action {selected} is returned by SelectAction()!")
                print("Selecting random action instead!")
                selected = random.choice(actions_copy)
                if self.displayer is not None:
                    self.displayer.TimeOutWarning(self,agent_index)
                self.warnings[agent_index] += 1
                self.warning_positions.append((agent_index,action_counter))

            random.seed(self.seed_list[self.seed_idx])
            self.seed_idx += 1
            history["actions"].append({action_counter:{"agent_id":self.game_rule.current_agent_index,"action":selected}})
            action_counter += 1
            self.game_rule.update(selected)
            random.seed(self.seed_list[self.seed_idx])
            self.seed_idx += 1

            if self.displayer is not None:
                self.displayer.ExcuteAction(agent_index,selected, self.game_rule.current_game_state)

            if self.warnings[agent_index] == self.warning_limit:
                history = self._EndGame(self.game_rule.num_of_agent,history,isTimeOut=True,id=agent_index)
                return history
                
        ##TODO: new!!
        for i in range(len(self.agents)):
            agent = self.agents[i]
            game_state = self.game_rule.current_game_state
            actions = self.game_rule.getLegalActions(game_state, i)
            if "final" in dir(agent):
                agent.final((copy.deepcopy(game_state), copy.deepcopy(actions)))
        ##

        # Score agent bonuses
        return self._EndGame(self.game_rule.num_of_agent,history,isTimeOut=False)
            

class GameReplayer:
    def __init__(self,GameRule,replay, displayer = None):
        self.replay = replay
                    
        self.seed = self.replay["seed"]
        random.seed(self.seed)
        self.seed_list = [random.randint(0,1e10) for _ in range(1000)]
        self.seed_idx = 0

        self.num_of_agent = self.replay["num_of_agent"]
        self.agents_namelist = replay["agents_namelist"]
        self.warning_limit = replay["warning_limit"]
        self.warnings = [0]*self.num_of_agent
        self.warning_positions = replay["warning_positions"]
        self.game_rule = GameRule(self.num_of_agent)
        self.scores=replay["scores"]

        self.displayer = displayer
        if self.displayer is not None:
            self.displayer.InitDisplayer(self)           
  
    def Run(self):
        for item in self.replay["actions"]:
            (index, info), = item.items()
            selected = info["action"]
            agent_index = info["agent_id"]
            self.game_rule.current_agent_index = agent_index          

            random.seed(self.seed_list[self.seed_idx])
            self.seed_idx += 1
            self.game_rule.update(selected)
            random.seed(self.seed_list[self.seed_idx])
            self.seed_idx += 1
            if self.displayer is not None:
                if (agent_index,index) in self.warning_positions:
                    self.warnings[agent_index] += 1
                    self.displayer.TimeOutWarning(self,agent_index)
                self.displayer.ExcuteAction(agent_index,selected, self.game_rule.current_game_state)
        ##TODO: new!!
        for i in range(len(self.agents)):
            agent = self.agents[i]
            game_state = self.game_rule.current_game_state
            actions = self.game_rule.getLegalActions(game_state, i)
            if "final" in dir(agent):
                agent.final((copy.deepcopy(game_state), copy.deepcopy(actions)))
        ##
        if self.displayer is not None:
            self.displayer.EndGame(self.game_rule.current_game_state,self.scores)
