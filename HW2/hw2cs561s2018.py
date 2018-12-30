import copy, datetime
import pprint

SUCCESS = 'Yes'
FAILURE = 'No'
TernaryConst = 'UEFA'
TIMELIMIT = 175
INPUT_FILE_NAME = 'test_cases/50.txt'
OUTPUT_FILE_NAME = 'output.txt'
GRP_PREFIX = 'GROUP'

def search(csp):
  start_time = datetime.datetime.now()
  result = backtrack({}, csp['variables'], csp, start_time)

  if result == FAILURE:
    return result
  else:
    return {i: v[0] for i, v in result.iteritems()}

def backtrack(assignments, unassigned, csp, start_time):
  # time elapse check
  time_elapsed = datetime.datetime.now() - start_time
  if time_elapsed.seconds > TIMELIMIT:  # time limit : 180 sec
    return FAILURE

  if chkFinished(unassigned):
    return assignments
  var = select_unassigned_variable(unassigned)
  values = ordering_values(var, assignments, unassigned, csp)
  del unassigned[var]

  for value in values:
    assignments[var] = [value]
    legal_v = enforce_consistency(assignments, unassigned, csp)
    if chkEmpty(legal_v):
      continue  # A variable has no legal values.
    unassign = {}
    for var, val in legal_v.iteritems():
      if var not in assignments:
        unassign.update({var: val})
    result = backtrack(assignments.copy(), unassign, csp, start_time)
    if result != FAILURE:
      return result

  return FAILURE

def chkFinished(unassigned):
  return len(unassigned) == 0

def chkEmpty(v):
  return any((len(values) == 0 for values in v.itervalues()))

def partial_assignment(assignments, unassigned):
  v = unassigned.copy()
  v.update(assignments)
  return v

def enforce_consistency(assignments, unassigned, csp):
  def remove_inconsistent_values(x, y, constraint, variables):
    #valid_tail_values = [t for t in variables[tail] if any((constraint(h, t) for h in variables[head]))]
    valid_tail_values = []
    for t in variables[y]:
      if any((constraint(h, t) for h in variables[x])):
        valid_tail_values.append(t)
    removed = len(variables[y]) != len(valid_tail_values)
    variables[y] = valid_tail_values
    return removed

  def recheck_constraints(node):
    new_csp = []
    for h, t, c in csp['constraints']:
      if h == node:
        new_csp.append((h,t,c))

    return new_csp

  const_queue, variables = csp['constraints'][:], partial_assignment(assignments, unassigned)
  while len(const_queue):
    x, y, constraint = const_queue.pop(0)

    if remove_inconsistent_values(x, y, constraint, variables):
      const_queue.extend(recheck_constraints(y))  # RECHECK
  return variables

def select_unassigned_variable(unassigned):
  # Select Most Constrained Variable from unassigned variables
  return min(unassigned.keys(), key=lambda k: len(unassigned[k]))

def ordering_values(var, assignments, unassigned, csp):

  def countingVal(vars):
    return sum((len(vars[v]) for v in unassigned if v != var))

  def eliminatingVal(val):
    assignments[var] = [val]
    new_vals = countingVal(enforce_consistency(assignments, unassigned, csp))
    del assignments[var]
    return new_vals

  # Orders an unassigned variable according to the Least Constraining Value
  return sorted(unassigned[var], key=eliminatingVal, reverse=True)


with open(INPUT_FILE_NAME, 'r') as f:
  groupNum = f.readline().strip()
  potNum = int(f.readline().strip())
  pot = {}
  for i in range(potNum):
    pot[i] = f.readline().strip().split(",")

  conf = {}
  for line in f:
    a = line.strip().split(":")
    conf[a[0]] = a[1].split(",")

  constraints = {}
  tmpPot = []
  for j in range(potNum):
    for k in range(len(pot[j])):
      key = pot[j][k]
      cons = list()
      for i in range(len(pot[j])):
        if(key != pot[j][i]):
          cons.append(pot[j][i])
      constraints[key] = cons

  UEFA = list()
  for i in conf.keys():
    if conf[i][0] != 'None' and i != TernaryConst:
      for k in conf[i]:
        constraints[k] = list(set(constraints[k]+conf[i]))
        constraints[k].remove(k)

  setUEFA = {}
  for country in constraints.keys():
    grpUEFA = copy.copy(conf[TernaryConst])
    if country in conf[TernaryConst]:
      grpUEFA.remove(country)
      for i in constraints[country]:
        if i in conf[TernaryConst]:
          grpUEFA.remove(i)
      setUEFA.update({country : grpUEFA})

  #print setUEFA

  matchUEFA = {}
  for i in setUEFA.keys():
    for j in setUEFA[i]:
      if i in setUEFA[j]:
        if i not in matchUEFA and j not in matchUEFA:
          #if len(matchUEFA)<=(int(groupNum)-1):
            matchUEFA.update({i:j})
            matchUEFA.update({j:i})

  #print str(len(matchUEFA))
  #print str(matchUEFA)

  unmatch = {}

  for i in matchUEFA.keys():
    grpmatchUEFA = copy.copy(conf[TernaryConst])
    grpmatchUEFA.remove(i)
    grpmatchUEFA.remove(matchUEFA[i])
    unmatch.update({i:grpmatchUEFA})

  #print "unmatch:" + str(unmatch)

  for country in constraints:
    if country in unmatch:
        constraints[country] = list(set(constraints[country]+unmatch[country]))

#print "constraints : " + str(constraints)

grpList = [GRP_PREFIX + str(i+1) for i in range(int(groupNum))]

def diff(i,j):
  return i != j

wc = {}
wc['variables'] = {country:grpList for country in constraints.keys()}
wc['constraints'] = [(s1, s2, diff) for s1 in constraints.keys() for s2 in constraints[s1]]

def print_output(status, outputResult):
  wfile = open(OUTPUT_FILE_NAME, "w")
  output = status + "\n"
  for grp in outputResult.keys():
    for grpElement in range(len(outputResult[grp])):
      if grpElement != len(outputResult[grp])-1:
        output+=str(outputResult[grp][grpElement])+ ","
      else:
        output+=str(outputResult[grp][grpElement])+ "\n"
  wfile.write(output)

result = search(wc)
#print result
status = SUCCESS

if result == FAILURE or not all((result[s1] != result[s2] for s1 in constraints.keys() for s2 in constraints[s1])):
  status = FAILURE
  print_output(status, {})
else:
  outputResult = {}

  for i in grpList:
    outputResult.update({i:[]})
  for i in result.keys():
    outputResult[result[i]].append(i)

  print_output(status, outputResult)
