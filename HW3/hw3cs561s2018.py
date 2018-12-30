import random
import itertools
import operator

argmin = min
argmax = max

def vector_add(a, b):
    """Component-wise addition of two vectors."""
    return tuple(map(operator.add, a, b))

orientations = EAST, RUN_EAST, NORTH, RUN_NORTH, WEST, RUN_WEST, SOUTH, RUN_SOUTH = [(1, 0), (2, 0), (0, 1), (0, 2), (-1, 0), (-2, 0), (0, -1), (0, -2)]
turns = LEFT, RIGHT, RUN, WALK = (+2, -2, +1, -1)

def turn_heading(heading, inc, headings=orientations):
    return headings[(headings.index(heading) + inc) % len(headings)]

def turn_left(heading):
    return turn_heading(heading, LEFT)

def turn_right(heading):
    return turn_heading(heading, RIGHT)


def isnumber(x):
    """Is x a number?"""
    return hasattr(x, '__int__')

def print_table(table, header=None, sep='   ', numfmt='{}'):
    justs = ['rjust' if isnumber(x) else 'ljust' for x in table[0]]

    if header:
        table.insert(0, header)

    table = [[numfmt.format(x) if isnumber(x) else x for x in row]
             for row in table]

    sizes = list(
        map(lambda seq: max(map(len, seq)),
            list(zip(*[map(str, row) for row in table]))))

    for row in table:
        print(sep.join(getattr(
            str(x), j)(size) for (j, size, x) in zip(justs, sizes, row)))

class MDP:

    def __init__(self, init, actlist, terminals, transitions=None, reward=None, states=None, gamma=0.7):
        if not (0 < gamma <= 1):
            raise ValueError("An MDP must have 0 < gamma <= 1")

        self.states = states or self.get_states_from_transitions(transitions)
        self.init = init

        if isinstance(actlist, list):
            self.actlist = actlist

        elif isinstance(actlist, dict):
            self.actlist = actlist

        self.terminals = terminals
        self.transitions = transitions or {}
        if not self.transitions:
            print("Warning: Transition table is empty.")

        self.gamma = gamma

        self.reward = reward or {s: 0 for s in self.states}

    def R(self, state):
        return self.reward[state]

    def T(self, state, action):
        if not self.transitions:
            raise ValueError("Transition model is missing")
        else:
            return self.transitions[state][action]

    def actions(self, state):
        if state in self.terminals:
            return [None]
        else:
            return self.actlist

    def get_states_from_transitions(self, transitions):
        if isinstance(transitions, dict):
            s1 = set(transitions.keys())
            s2 = set(tr[1] for actions in transitions.values()
                     for effects in actions.values()
                     for tr in effects)
            return s1.union(s2)
        else:
            print('Could not retrieve states from transitions')
            return None

class GridMDP(MDP):
    def __init__(self, grid, Pr_walk, Pr_run, terminals, gamma, init=(0, 0)):
        grid.reverse()  # sbecause we want row 0 on bottom, not on top
        reward = {}
        states = set()
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.grid = grid
        for x in range(self.cols):
            for y in range(self.rows):
                if grid[y][x]:
                    states.add((x, y))
                    reward[(x, y)] = grid[y][x]
        self.states = states
        actlist = orientations
        transitions = {}
        for s in states:
            transitions[s] = {}
            for a in actlist:
                transitions[s][a] = self.calculate_T(s, a, Pr_walk, Pr_run)
        MDP.__init__(self, init, actlist=actlist,
                     terminals=terminals, transitions=transitions,
                     reward=reward, states=states, gamma=gamma)

    def calculate_T(self, state, action, Pr_walk, Pr_run):
        if action[0] == 2 or action[0] == -2 or action[1] == 2 or action[1] == -2:
            return [(Pr_run, self.go(state, action)),
                    ((1-Pr_run)/2, self.go(state, turn_left(action))),
                    ((1-Pr_run)/2, self.go(state, turn_right(action)))
                    ]
        elif action[0] == 1 or action[0] == -1 or action[1] == 1 or action[1] == -1:
            return [(Pr_walk, self.go(state, action)),
                    ((1-Pr_walk)/2, self.go(state, turn_left(action))),
                    ((1-Pr_walk)/2, self.go(state, turn_right(action)))
                    ]
        else:
            return [(0.0, state)]

    def T(self, state, action):
        return self.transitions[state][action] if action else [(0.0, state)]

    def go(self, state, direction):
        state1 = vector_add(state, direction)
        if direction[0] == 2 or direction[0] == -2 or direction[1] == 2 or direction[1] == -2:
            prev_state1 = tuple(map(lambda a,b: (a+b)/2, state, state1))
            if prev_state1 in self.states:
                return state1 if state1 in self.states else state
            else:
                return state
        elif direction[0] == 1 or direction[0] == -1 or direction[1] == 1 or direction[1] == -1:
            return state1 if state1 in self.states else state

    def to_grid(self, mapping):
        return list(reversed([[mapping.get((x, y), None)
                               for x in range(self.cols)]
                              for y in range(self.rows)]))

    def to_arrows(self, policy):
        chars = {(1, 0): 'Walk Right',(2, 0): 'Run Right', (0, 1): 'Walk Up', (0, 2): 'Run Up',
                 (-1, 0): 'Walk Left', (-2, 0): 'Run Left', (0, -1): 'Walk Down', (0, -2): 'Run Down',None: 'Exit'}
        return self.to_grid({s: chars[a] for (s, a) in policy.items()})

def value_iteration(mdp, epsilon=0.1):
    U1 = {s: 0 for s in mdp.states}
    R, T, gamma = mdp.R, mdp.T, mdp.gamma
    epsilon_counter = 0
    prev_delta = 0
    while True:
        U = U1.copy()
        delta = 0
        for s in mdp.states:
            tmpSum_walk = [sum(p * U[s1] for (p, s1) in T(s, a)) for a in mdp.actions(s) if check_run(a) == 0]
            tmpSum_run = [sum(p * U[s1] for (p, s1) in T(s, a)) for a in mdp.actions(s) if check_run(a) == 1]
            tmpSum = list(itertools.chain.from_iterable([tmpSum_walk,tmpSum_run]))

            tmpMax = max(tmpSum)
            idxMax = tmpSum.index(tmpMax)

            if idxMax < 4:
                tmpReward = R(s)[1]
            else:
                tmpReward = R(s)[0]

            U1[s] = tmpReward + gamma * tmpMax

            # U1[s] = gamma * max(sum(p * U[s1] for (p, s1) in T(s, a)) for a in mdp.actions(s))
            delta = max(delta, abs(U1[s] - U[s]))

        # print("==============================================================================")
        # print_table(print_grid(U))
        # print("delta:" + str(delta))

        if round(prev_delta,3) == round(delta,3):
            epsilon_counter+=1

        if delta < epsilon * (1 - gamma) / gamma or epsilon_counter > 10:
            return U
        prev_delta = delta

def check_run(action):
    if action == None:
        return 0;
    else:
        if action[0] == 2 or action[0] == -2 or action[1] == 2 or action[1] == -2:
            return 1
        else:
            return 0


def best_policy(mdp, U):
    pi = {}
    for s in mdp.states:
        pi[s] = argmax(mdp.actions(s), key=lambda a: expected_utility(a, s, U, mdp))
    return pi


def expected_utility(a, s, U, mdp):
    return sum(p * U[s1] for (p, s1) in mdp.T(s, a))

def print_grid(mapping):
        return list(reversed([[mapping.get((x, y), None)
                               for x in range(6)]
                              for y in range(5)]))

def getInputs():
    INPUT_FILE_NAME = "input.txt"

    with open(INPUT_FILE_NAME, 'r') as f:
        GRID_ROW, GRID_COL = map(int,f.readline().strip().split(","))

        WALL_CELLS_NUM = int(f.readline().strip())
        WALL_CELLS = list()
        WALL_CELLS_POSITION = list()
        for i in range(WALL_CELLS_NUM):
            WALL_CELLS_POSITION = f.readline().strip().split(",")
            WALL_CELLS.append((int(WALL_CELLS_POSITION[0]),int(WALL_CELLS_POSITION[1])))

        TERMINAL_STATES_NUM = int(f.readline().strip())
        TERMINAL_STATES = list()
        T_REWARD = list()
        for i in range(TERMINAL_STATES_NUM):
            terminal_line = list()
            terminal_line = f.readline().strip().split(",")
            T_POSITION = (int(terminal_line[0]),int(terminal_line[1]))
            T_REWARD.append(terminal_line[2])
            TERMINAL_STATES.append(T_POSITION)

        Pr_walk, Pr_run = map(float,f.readline().strip().split(","))

        REWARD = list()
        REWARD = map(float,f.readline().strip().split(","))

        DISCOUNT_FACTOR = float(f.readline().strip())

        #print(GRID_ROW,GRID_COL, WALL_CELLS, TERMINAL_STATES, T_REWARD,Pr_walk, Pr_run, REWARD, DISCOUNT_FACTOR)

        gridRow = list()
        for i in range(int(GRID_ROW)):
            gridColumn = list()
            for j in range(int(GRID_COL)):
                if (GRID_ROW-i,j+1) in WALL_CELLS:
                    tmpList = None
                    gridColumn.append(tmpList)
                elif (GRID_ROW-i,j+1) in TERMINAL_STATES:
                    idx = TERMINAL_STATES.index((GRID_ROW-i,j+1))
                    tmpList = [float(T_REWARD[idx]),float(T_REWARD[idx])]
                    gridColumn.append(tmpList)
                else:
                    tmpList = REWARD
                    gridColumn.append(tmpList)
            gridRow.append(gridColumn)
        #print_table(gridRow)

        for i in range(len(TERMINAL_STATES)):
            TERMINAL_STATES[i] = (TERMINAL_STATES[i][1]-1, TERMINAL_STATES[i][0]-1)

        x = GridMDP(gridRow, Pr_walk, Pr_run, terminals=TERMINAL_STATES, gamma=DISCOUNT_FACTOR)
        util = value_iteration(x)
        pi = best_policy(x, util)
        move_i = x.to_arrows(pi)
        print_output(move_i)
        #print_table(move_i)

def print_output(outputResult):
    OUTPUT_FILE_NAME = "output.txt"
    output = ""
    wfile = open(OUTPUT_FILE_NAME, "w")
    for i in range(len(outputResult)):
        for j in range(len(outputResult[i])):
            if j != len(outputResult[i])-1:
                output+=str(outputResult[i][j])+ ","
            else:
                output+=str(outputResult[i][j])+ "\n"
    wfile.write(output)

def makingGrid():
    print()

## start
getInputs()



