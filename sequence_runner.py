# INFORMATION ------------------------------------------------------------------------------------------------------- #

# Author:  Steven Spratley, extending code by Guang Ho and Michelle Blom
# Date:    04/01/2021
# Purpose: Implements "Sequence" for the COMP90054 competitive game environment

# IMPORTS ------------------------------------------------------------------------------------------------------------#

import sys
import os
import importlib
import traceback
import datetime
import time
import pickle
import random
from Sequence.sequence_model import SequenceGameRule as GameRule
from Sequence.sequence_displayer import TextDisplayer,GUIDisplayer
from template import Agent as DummyAgent
from game import Game, GameReplayer
from optparse import OptionParser

# CONSTANTS ----------------------------------------------------------------------------------------------------------#

error_index= ["red_team_load","blue_team_load"]

# CLASS DEF ----------------------------------------------------------------------------------------------------------#

def loadAgent(file_list,name_list,superQuiet = True):
    agents = [None]*4
    load_errs = {}
    print(f"path is {file_list}")
    for i,agent_file_path in enumerate(file_list):
        agent_temp = None
        print(f"path is {agent_file_path}")

        try:
            mymodule = importlib.import_module(agent_file_path)
            agent_temp = mymodule.myAgent(i)
        except (NameError, ImportError, IOError):
            print('Error: The team "' + agent_file_path + '" could not be loaded! ', file=sys.stderr)
            traceback.print_exc()
            pass
        except:
            pass

        # if student's agent does not exist, use random agent.
        if agent_temp != None:
            agents[i] = agent_temp
            if not superQuiet:
                print ('Agent {} team {} agent {} loaded'.format(i,name_list[i],file_list[i]))
        else:
            agents[i] = DummyAgent(i)
            load_errs[error_index[i]] = '[Error] Agent {} team {} agent {} cannot be loaded'\
                .format(i,name_list[i],".".join((file_list[i]).split(".")[-2:]))
        
    return agents, load_errs


class HidePrint:
    # setting output stream
    def __init__(self,flag,file_path,f_name):
        self.flag = flag
        self.file_path = file_path
        self.f_name = f_name
        self._original_stdout = sys.stdout

    def __enter__(self):
        if self.flag:
            if not os.path.exists(self.file_path):
                os.makedirs(self.file_path)
            sys.stdout = open(self.file_path+"/log-"+self.f_name+".log", 'w')
            sys.stderr = sys.stdout
        else:
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = sys.stdout

    # Restore
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
        sys.stderr = sys.stdout


def run(options,valid_game,msg):

    # text displayer, will disable GUI
    displayer = GUIDisplayer(options.delay)
    if options.textgraphics:
        displayer = TextDisplayer()
    elif options.quiet or options.superQuiet:
        displayer = None

    agents_names = [options.redName, options.blueName]*2
    for i in range(len(agents_names)):
        agents_names[i] = agents_names[i].replace(" ","_")

    # if random seed is not provide, using timestamp
    if options.setRandomSeed == 90054:
        random_seed = int(str(time.time()).replace('.', ''))
    else:
        random_seed = options.setRandomSeed
    
    # make sure random seed is traceable
    random.seed(random_seed)
    seed_list = [random.randint(0,1e10) for _ in range(1000)]
    seed_idx = 0

    num_of_warning = options.numOfWarnings
    file_path = options.output

    if options.replay != None:
        if not options.superQuiet:
            print('Replaying recorded game %s.' % options.replay)
        replay_dir = options.replay
        replay = pickle.load(open(replay_dir,'rb'),encoding="bytes")
        GameReplayer(GameRule,replay,displayer).Run()
    else: 
        games_results = [(0,0,0,0,0,0,0)]
        results = {"succ":valid_game}
        for i in range(options.multipleGames):
            #Load each agent twice, for two teams of two.
            agents,load_errs = loadAgent([options.red, options.blue, options.red, options.blue], 
                                          agents_names, superQuiet=options.superQuiet)
            is_load_err = False
            for i,err in load_errs.items():
                msg += "{} {}\n".format(i,err)
                if not options.superQuiet:
                    print(i,err)
                is_load_err = True
        
            random_seed=seed_list[seed_idx]
            seed_idx += 1

            if is_load_err:
                results["load_errors"] = load_errs
                results["succ"]=False
                valid_game = False

            f_name = agents_names[0]+'-vs-'+agents_names[1]+"-"+datetime.datetime.now().strftime("%d-%b-%Y-%H-%M-%S-%f")
            
            gr = Game(GameRule,
                        agents,
                        num_of_agent = options.num_of_agent,
                        seed=random_seed,
                        time_limit=options.warningTimeLimit,
                        warning_limit=num_of_warning,
                        displayer=displayer,
                        agents_namelist=agents_names)
            if not options.print:
                with HidePrint(options.saveLog,file_path,f_name):
                    print("Following are the print info for loading:\n{}\n".format(msg))
                    print("\n-------------------------------------\n")
                    print("Following are the print info from the game:\n")
                    if valid_game:          
                        replay = gr.Run()
                    else:
                        print("Invalid game. No game played.\n")
            else:
                print("Following are the print info for loading:\n{}\n".format(msg))
                print("\n-------------------------------------\n")
                print("Following are the print info from the game:\n")
                if valid_game:      
                    replay = gr.Run()
                else:
                    print("Invalid game. No game played.\n")
                    
            if valid_game:
                _,_,r_total,b_total,r_win,b_win,tie = games_results[len(games_results)-1]
                r_score = replay["scores"][0] + replay["scores"][2] # Two teams of two players, so scores are summed.
                b_score = replay["scores"][1] + replay["scores"][3]
                if r_score==b_score:
                    tie = tie + 1
                elif r_score<b_score:
                    b_win = b_win + 1
                else:
                    r_win = r_win + 1

                # adding this to avoid -1 in the score
                r_score = max(r_score,0)
                b_score = max(b_score,0)
                r_total = r_total+r_score
                b_total = b_total+b_score
                if not options.superQuiet:
                    print("Result of game ({}/{}): Agent {} earned {} points; Agent {} earned {} points\n".format(i+1,options.multipleGames,agents_names[0],r_score,agents_names[1],b_score))
                games_results.append((r_score,b_score,r_total,b_total,r_win,b_win,tie))

                if options.saveGameRecord:
                    if not os.path.exists(file_path):
                        os.makedirs(file_path)
                    if not options.superQuiet:
                        print("Game ({}/{}) has been recorded!\n".format(i+1,options.multipleGames))
                    record = pickle.dumps(replay)
                    with open(file_path+"/replay-"+f_name+".replay",'wb') as f:
                        f.write(record)
            
        if valid_game:
            _,_,r_total,b_total,r_win,b_win,tie = games_results[len(games_results)-1]
            r_avg = r_total/options.multipleGames
            b_avg = b_total/options.multipleGames
            r_win_rate = r_win / options.multipleGames *100
            b_win_rate = b_win / options.multipleGames *100
            if not options.superQuiet:
                print(
                    "Over {} games: \nAgent {} earned {:+.2f} points in average and won {} games, winning rate {:.2f}%; \nAgent {} earned {:+.2f} points in average and won {} games, winning rate {:.2f}%; \nAnd {} games tied.".format(options.multipleGames,
                    agents_names[0],r_avg,r_win,r_win_rate,agents_names[1],b_avg,b_win,b_win_rate,tie))

            # return results as statistics
            results["r_total"] = r_total
            results["b_total"] = b_total
            results["r_win"] = r_win
            results["b_win"] = b_win
            results["r_win_rate"] = r_win_rate
            results["b_win_rate"] = b_win_rate
            results["r_name"] = agents_names[0]
            results["b_name"] = agents_names[1]
            results["fileName"] = f_name
            results["load_errs"] = load_errs
            results["tie"] = tie
            results["succ"] = True

        return results


def loadParameter():

    """
    Processes the command used to run Sequence from the command line.
    """
    usageStr = """
    USAGE:      python runner.py <options>
    EXAMPLES:   (1) python runner.py
                    - starts a game with two NaiveAgent
                (2) python runner.py -r naive_agent -b myAgent
                    - starts a fully automated game where the red team is a NaiveAgent and blue team is myAgent
    """
    parser = OptionParser(usageStr)

    parser.add_option('-r', '--red', help='Red team agent file (default: samples.random)', default='samples.random')
    parser.add_option('-b', '--blue', help='Blue team agent file (default: samples.random)', default='samples.random')
    parser.add_option('--redName', help='Red team name (default: Red RandomAgent)', default='Red RandomAgent')
    parser.add_option('--blueName', help='Blue team name (default: Blue RandomAgent)',default='Blue RandomAgent')
    parser.add_option('-t','--textgraphics', action='store_true', help='Display output as text only (default: False)', default=False)
    parser.add_option('-q','--quiet', action='store_true', help='No text nor graphics output, only show game info', default=False)
    parser.add_option('-Q', '--superQuiet', action='store_true', help='No output at all', default=False)
    parser.add_option('-w', '--warningTimeLimit', type='float',help='Time limit for a warning of one move in seconds (default: 1)', default=1.0)
    parser.add_option('--startRoundWarningTimeLimit', type='float',help='Time limit for a warning of initialization for each round in seconds (default: 5)', default=5.0)
    parser.add_option('-n', '--numOfWarnings', type='int',help='Num of warnings a team can get before fail (default: 3)', default=3)
    parser.add_option('-m', '--multipleGames', type='int',help='Run multiple games in a roll', default=1)
    parser.add_option('--setRandomSeed', type='int',help='Set the random seed, otherwise it will be completely random (default: 90054)', default=90054)
    parser.add_option('-s','--saveGameRecord', action='store_true', help='Writes game histories to a file (named by teams\' names and the time they were played) (default: False)', default=False)
    parser.add_option('-o','--output', help='output directory for replay and log (default: output)',default='output')
    parser.add_option('-l','--saveLog', action='store_true',help='Writes agent printed information into a log file(named by the time they were played)', default=False)
    parser.add_option('--replay', default=None, help='Replays a recorded game file by a relative path')
    parser.add_option('--delay', type='float', help='Delay action in a play or replay by input (float) seconds (default 0.1)', default=0.1)
    parser.add_option('-p','--print', action='store_true', help='Print all the output in terminal when playing games, will diable \'-l\' automatically. (default: False)', default=False)
    parser.add_option('--num_of_agent', type='int',help='num_of_agent', default=4)


    options, otherjunk = parser.parse_args(sys.argv[1:] )
    assert len(otherjunk) == 0, "Unrecognized options: " + str(otherjunk)

    #quick fixed on the naming, might need to be changed when the contest environment is fixed
    options.red = "agents."+options.red
    options.blue = "agents."+options.blue

    return options

# MAIN ---------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':

    """
    The main function called when advance_model.py is run
    from the command line:

    > python runner.py

    See the usage string for more details.

    > python runner.py --help
    """
    msg = ""
    options = loadParameter()
    run(options,True,msg)

# END FILE -----------------------------------------------------------------------------------------------------------#