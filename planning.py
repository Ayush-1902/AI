"""Planning (Chapters 10-11)
"""

import itertools
from search import Node
from utils import Expr, expr, first
from logic import FolKB
from collections import deque


class PDDL:
    """
    Planning Domain Definition Language (PDDL) used to define a search problem.
    It stores states in a knowledge base consisting of first order logic statements.
    The conjunction of these logical statements completely defines a state.
    """

    def __init__(self, initial_state, actions, goal_test):
        self.kb = FolKB(initial_state)
        self.actions = actions
        self.goal_test_func = goal_test

    def goal_test(self):
        return self.goal_test_func(self.kb)

    def act(self, action):
        """
        Performs the action given as argument.
        Note that action is an Expr like expr('Remove(Glass, Table)') or expr('Eat(Sandwich)')
        """       
        action_name = action.op
        args = action.args
        list_action = first(a for a in self.actions if a.name == action_name)
        if list_action is None:
            raise Exception("Action '{}' not found".format(action_name))
        if not list_action.check_precond(self.kb, args):
            raise Exception("Action '{}' pre-conditions not satisfied".format(action))
        list_action(self.kb, args)


class Action:
    """
    Defines an action schema using preconditions and effects.
    Use this to describe actions in PDDL.
    action is an Expr where variables are given as arguments(args).
    Precondition and effect are both lists with positive and negated literals.
    Example:
    precond_pos = [expr("Human(person)"), expr("Hungry(Person)")]
    precond_neg = [expr("Eaten(food)")]
    effect_add = [expr("Eaten(food)")]
    effect_rem = [expr("Hungry(person)")]
    eat = Action(expr("Eat(person, food)"), [precond_pos, precond_neg], [effect_add, effect_rem])
    """

    def __init__(self, action, precond, effect):
        self.name = action.op
        self.args = action.args
        self.precond_pos = precond[0]
        self.precond_neg = precond[1]
        self.effect_add = effect[0]
        self.effect_rem = effect[1]

    def __call__(self, kb, args):
        return self.act(kb, args)

    def substitute(self, e, args):
        """Replaces variables in expression with their respective Propositional symbol"""
        new_args = list(e.args)
        for num, x in enumerate(e.args):
            for i, _ in enumerate(self.args):
                if self.args[i] == x:
                    new_args[num] = args[i]
        return Expr(e.op, *new_args)

    def check_precond(self, kb, args):
        """Checks if the precondition is satisfied in the current state"""
        # check for positive clauses
        for clause in self.precond_pos:
            if self.substitute(clause, args) not in kb.clauses:
                return False
        # check for negative clauses
        for clause in self.precond_neg:
            if self.substitute(clause, args) in kb.clauses:
                return False
        return True

    def act(self, kb, args):
        """Executes the action on the state's kb"""
        # check if the preconditions are satisfied
        if not self.check_precond(kb, args):
            raise Exception("Action pre-conditions not satisfied")
        # remove negative literals
        for clause in self.effect_rem:
            kb.retract(self.substitute(clause, args))
        # add positive literals
        for clause in self.effect_add:
            kb.tell(self.substitute(clause, args))


class UnaryAction:
    """
    Defines an action schema using preconditions and effects.
    Use this to describe actions in PDDL.
    action is an Expr where variables are given as arguments(args).
    Precondition and effect are both lists with positive and negative literals.
    Negative preconditions and effects are defined by adding a 'Not' before the name of the clause
    Example:
    precond = [expr("Human(person)"), expr("Hungry(Person)"), expr("NotEaten(food)")]
    effect = [expr("Eaten(food)"), expr("Hungry(person)")]
    eat = UnaryAction(expr("Eat(person, food)"), precond, effect)
    """

    def __init__(self, action, precond, effect):
        self.name = action.op
        self.args = action.args
        self.precond = precond
        self.effect = effect

    def __call__(self, kb, args):
        return self.act(kb, args)

    def substitute(self, e, args):
        """Replaces variables in expression with their respective Propositional symbol"""

        new_args = list(e.args)
        for num, x in enumerate(e.args):
            for i, _ in enumerate(self.args):
                if self.args[i] == x:
                    new_args[num] = args[i]
        return Expr(e.op, *new_args)

    def check_precond(self, kb, args):
        """Checks if the precondition is satisfied in the current state"""

        for clause in self.precond:
            if self.substitute(clause, args) not in kb.clauses:
                return False
        return True

    def act(self, kb, args):
        """Executes the action on the state's knowledge base"""

        if not self.check_precond(kb, args):
            raise Exception('UnaryAction pre-conditions not satisfied')
        for clause in self.effect:
            kb.tell(self.substitute(clause, args))
            if clause.op[:3] == 'Not':
                new_clause = Expr(clause.op[3:], *clause.args)

                if kb.ask(self.substitute(new_clause, args)) is not False:
                    kb.retract(self.substitute(new_clause, args))
            else:
                new_clause = Expr('Not' + clause.op, *clause.args)

                if kb.ask(self.substitute(new_clause, args)) is not False:    
                    kb.retract(self.substitute(new_clause, args))


def air_cargo():
    """Air cargo problem"""

    init = [expr('At(C1, SFO)'),
            expr('At(C2, JFK)'),
            expr('At(P1, SFO)'),
            expr('At(P2, JFK)'),
            expr('Cargo(C1)'),
            expr('Cargo(C2)'),
            expr('Plane(P1)'),
            expr('Plane(P2)'),
            expr('Airport(SFO)'),
            expr('Airport(JFK)')]

    def goal_test(kb):
        required = [expr('At(C1, JFK)'), expr('At(C2, SFO)')]
        return all(kb.ask(q) is not False for q in required)

    # Actions
    # Load
    precond = [expr('At(c, a)'), expr('At(p, a)'), expr('Cargo(c)'), expr('Plane(p)'), expr('Airport(a)')]
    effect = [expr('In(c, p)'), expr('NotAt(c, a)')]
    load = UnaryAction(expr('Load(c, p, a)'), precond, effect)

    # Unload
    precond = [expr('In(c, p)'), expr('At(p, a)'), expr('Cargo(c)'), expr('Plane(p)'), expr('Airport(a)')]
    effect = [expr('At(c, a)'), expr('NotIn(c, p)')]
    unload = UnaryAction(expr('Unload(c, p, a)'), precond, effect)

    # Fly
    precond = [expr('At(p, f)'), expr('Plane(p)'), expr('Airport(f)'), expr('Airport(to)')]
    effect = [expr('At(p, to)'), expr('NotAt(p, f)')]
    fly = UnaryAction(expr('Fly(p, f, to)'), precond, effect)

    return PDDL(init, [load, unload, fly], goal_test)


def spare_tire():
    """Spare tire problem"""

    init = [expr('Tire(Flat)'),
            expr('Tire(Spare)'),
            expr('At(Flat, Axle)'),
            expr('At(Spare, Trunk)')]

    def goal_test(kb):
        required = [expr('At(Spare, Axle)'), expr('At(Flat, Ground)')]
        return all(kb.ask(q) is not False for q in required)

    # Actions
    # Remove
    precond = [expr('At(obj, loc)')]
    effect = [expr('At(obj, Ground)'), expr('NotAt(obj, loc)')]
    remove = UnaryAction(expr('Remove(obj, loc)'), precond, effect)

    # PutOn
    precond = [expr('Tire(t)'), expr('At(t, Ground)'), expr('NotAt(Flat, Axle)')]
    effect = [expr('At(t, Axle)'), expr('NotAt(t, Ground)')]
    put_on = UnaryAction(expr('PutOn(t, Axle)'), precond, effect)

    # LeaveOvernight
    precond = []
    effect = [expr('NotAt(Spare, Ground)'), expr('NotAt(Spare, Axle)'), expr('NotAt(Spare, Trunk)'), expr('NotAt(Flat, Ground)'), expr('NotAt(Flat, Axle)'), expr('NotAt(Flat, Trunk)')]
    leave_overnight = UnaryAction(expr('LeaveOvernight'), precond, effect)

    return PDDL(init, [remove, put_on, leave_overnight], goal_test)


def three_block_tower():
    """Sussman Anomaly problem"""

    init = [expr('On(A, Table)'),
            expr('On(B, Table)'),
            expr('On(C, A)'),
            expr('Block(A)'),
            expr('Block(B)'),
            expr('Block(C)'),
            expr('Clear(B)'),
            expr('Clear(C)')]

    def goal_test(kb):
        required = [expr('On(A, B)'), expr('On(B, C)')]
        return all(kb.ask(q) is not False for q in required)

    # Actions
    # Move
    precond = [expr('On(b, x)'), expr('Clear(b)'), expr('Clear(y)'), expr('Block(b)'), expr('Block(y)')]
    effect = [expr('On(b, y)'), expr('Clear(x)'), expr('NotOn(b, x)'), expr('NotClear(y)')]
    move = UnaryAction(expr('Move(b, x, y)'), precond, effect)

    # MoveToTable
    precond = [expr('On(b, x)'), expr('Clear(b)'), expr('Block(b)')]
    effect = [expr('On(b, Table)'), expr('Clear(x)'), expr('NotOn(b, x)')]
    move_to_table = UnaryAction(expr('MoveToTable(b, x)'), precond, effect)

    return PDDL(init, [move, move_to_table], goal_test)


def have_cake_and_eat_cake_too():
    """Cake problem"""

    init = [expr('Have(Cake)')]

    def goal_test(kb):
        required = [expr('Have(Cake)'), expr('Eaten(Cake)')]
        return all(kb.ask(q) is not False for q in required)

    # Actions
    # Eat cake
    precond = [expr('Have(Cake)')]
    effect = [expr('Eaten(Cake)'), expr('NotHave(Cake)')]
    eat_cake = UnaryAction(expr('Eat(Cake)'), precond, effect)

    # Bake cake
    precond = [expr('NotHave(Cake)')]
    effect = [expr('Have(Cake)')]
    bake_cake = UnaryAction(expr('Bake(Cake)'), precond, effect)

    return PDDL(init, [eat_cake, bake_cake], goal_test)


def shopping_problem():
    init = [expr('At(Home)'), 
            expr('Sells(SM, Milk)'),
            expr('Sells(SM, Banana)'),
            expr('Sells(HW, Drill)')]

    def goal_test(kb):
        required = [expr('Have(Milk)'), expr('Have(Banana)'), expr('Have(Drill)')]
        return all(kb.ask(q) is not False for q in required)

    # Actions
    # Buy
    precond = [expr('At(store)'), expr('Sells(store, x)')]
    effect = [expr('Have(x)')]
    buy = UnaryAction(expr('Buy(x, store)'), precond, effect)

    # Go
    precond = [expr('At(x)')]
    effect = [expr('At(y)'), expr('NotAt(x)')]
    go = UnaryAction(expr('Go(x, y)'), precond, effect)

    return PDDL(init, [buy, go], goal_test)


class Level:
    """
    Contains the state of the planning problem
    and exhaustive list of actions which use the
    states as pre-condition.
    """

    def __init__(self, kb):
        """Initializes variables to hold state and action details of a level"""

        self.kb = kb
        # current state
        self.current_state = kb.clauses
        # current action to state link
        self.current_action_links = {}
        # current state to action link
        self.current_state_links = {}
        # current action to next state link
        self.next_action_links = {}
        # next state to current action link
        self.next_state_links = {}
        # mutually exclusive actions
        self.mutex = []

    def __call__(self, actions, objects):
        self.build(actions, objects)
        self.find_mutex()

    def separate(self, e):
        """Separates an iterable of elements into positive and negative parts"""

        positive = []
        negative = []
        for clause in e:
            if clause.op[:3] == 'Not':
                negative.append(clause)
            else:
                positive.append(clause)
        return positive, negative

    def find_mutex(self):
        """Finds mutually exclusive actions"""

        # Inconsistent effects
        pos_nsl, neg_nsl = self.separate(self.next_state_links)

        for negeff in neg_nsl:
            new_negeff = Expr(negeff.op[3:], *negeff.args)
            for poseff in pos_nsl:
                if new_negeff == poseff:
                    for a in self.next_state_links[poseff]:
                        for b in self.next_state_links[negeff]:
                            if {a, b} not in self.mutex:
                                self.mutex.append({a, b})

        # Interference will be calculated with the last step
        pos_csl, neg_csl = self.separate(self.current_state_links)

        # Competing needs
        for posprecond in pos_csl:
            for negprecond in neg_csl:
                new_negprecond = Expr(negprecond.op[3:], *negprecond.args)
                if new_negprecond == posprecond:
                    for a in self.current_state_links[posprecond]:
                        for b in self.current_state_links[negprecond]:
                            if {a, b} not in self.mutex:
                                self.mutex.append({a, b})

        # Inconsistent support
        state_mutex = []
        for pair in self.mutex:
            next_state_0 = self.next_action_links[list(pair)[0]]
            if len(pair) == 2:
                next_state_1 = self.next_action_links[list(pair)[1]]
            else:
                next_state_1 = self.next_action_links[list(pair)[0]]
            if (len(next_state_0) == 1) and (len(next_state_1) == 1):
                state_mutex.append({next_state_0[0], next_state_1[0]})
        
        self.mutex = self.mutex + state_mutex

    def build(self, actions, objects):
        """Populates the lists and dictionaries containing the state action dependencies"""

        for clause in self.current_state:
            p_expr = Expr('P' + clause.op, *clause.args)
            self.current_action_links[p_expr] = [clause]
            self.next_action_links[p_expr] = [clause]
            self.current_state_links[clause] = [p_expr]
            self.next_state_links[clause] = [p_expr]

        for a in actions:
            num_args = len(a.args)
            possible_args = tuple(itertools.permutations(objects, num_args))

            for arg in possible_args:
                if a.check_precond(self.kb, arg):
                    for num, symbol in enumerate(a.args):
                        if not symbol.op.islower():
                            arg = list(arg)
                            arg[num] = symbol
                            arg = tuple(arg)

                    new_action = a.substitute(Expr(a.name, *a.args), arg)
                    self.current_action_links[new_action] = []

                    for clause in a.precond:
                        new_clause = a.substitute(clause, arg)
                        self.current_action_links[new_action].append(new_clause)
                        if new_clause in self.current_state_links:
                            self.current_state_links[new_clause].append(new_action)
                        else:
                            self.current_state_links[new_clause] = [new_action]
                   
                    self.next_action_links[new_action] = []
                    for clause in a.effect:
                        new_clause = a.substitute(clause, arg)

                        self.next_action_links[new_action].append(new_clause)
                        if new_clause in self.next_state_links:
                            self.next_state_links[new_clause].append(new_action)
                        else:
                            self.next_state_links[new_clause] = [new_action]

    def perform_actions(self):
        """Performs the necessary actions and returns a new Level"""

        new_kb = FolKB(list(set(self.next_state_links.keys())))
        return Level(new_kb)


class Graph:
    """
    Contains levels of state and actions
    Used in graph planning algorithm to extract a solution
    """

    def __init__(self, pddl):
        self.pddl = pddl
        self.levels = [Level(pddl.kb)]
        self.objects = set(arg for clause in pddl.kb.clauses for arg in clause.args)

    def __call__(self):
        self.expand_graph()

    def expand_graph(self):
        """Expands the graph by a level"""

        last_level = self.levels[-1]
        last_level(self.pddl.actions, self.objects)
        self.levels.append(last_level.perform_actions())

    def non_mutex_goals(self, goals, index):
        """Checks whether the goals are mutually exclusive"""

        goal_perm = itertools.combinations(goals, 2)
        for g in goal_perm:
            if set(g) in self.levels[index].mutex:
                return False
        return True


class GraphPlan:
    """
    Class for formulation GraphPlan algorithm
    Constructs a graph of state and action space
    Returns solution for the planning problem
    """

    def __init__(self, pddl):
        self.graph = Graph(pddl)
        self.nogoods = []
        self.solution = []

    def check_leveloff(self):
        """Checks if the graph has levelled off"""

        check = (set(self.graph.levels[-1].current_state) == set(self.graph.levels[-2].current_state))

        if check:
            return True

    def extract_solution(self, goals, index):
        """Extracts the solution"""

        level = self.graph.levels[index]    
        if not self.graph.non_mutex_goals(goals, index):
            self.nogoods.append((level, goals))
            return

        level = self.graph.levels[index - 1]    

        # Create all combinations of actions that satisfy the goal    
        actions = []
        for goal in goals:
            actions.append(level.next_state_links[goal])    

        all_actions = list(itertools.product(*actions))    

        # Filter out non-mutex actions
        non_mutex_actions = []    
        for action_tuple in all_actions:
            action_pairs = itertools.combinations(list(set(action_tuple)), 2)        
            non_mutex_actions.append(list(set(action_tuple)))        
            for pair in action_pairs:            
                if set(pair) in level.mutex:
                    non_mutex_actions.pop(-1)
                    break
    

        # Recursion
        for action_list in non_mutex_actions:        
            if [action_list, index] not in self.solution:
                self.solution.append([action_list, index])

                new_goals = []
                for act in set(action_list):                
                    if act in level.current_action_links:
                        new_goals = new_goals + level.current_action_links[act]

                if abs(index) + 1 == len(self.graph.levels):
                    return
                elif (level, new_goals) in self.nogoods:
                    return
                else:
                    self.extract_solution(new_goals, index - 1)

        # Level-Order multiple solutions
        solution = []
        for item in self.solution:
            if item[1] == -1:
                solution.append([])
                solution[-1].append(item[0])
            else:
                solution[-1].append(item[0])

        for num, item in enumerate(solution):
            item.reverse()
            solution[num] = item

        return solution


def spare_tire_graphplan():
    """Solves the spare tire problem using GraphPlan"""

    pddl = spare_tire()
    graphplan = GraphPlan(pddl)

    def goal_test(kb, goals):
        return all(kb.ask(q) is not False for q in goals)

    goals = [expr('At(Spare, Axle)'), expr('At(Flat, Ground)')]

    while True:
        graphplan.graph.expand_graph()
        if (goal_test(graphplan.graph.levels[-1].kb, goals) and graphplan.graph.non_mutex_goals(goals, -1)):
            solution = graphplan.extract_solution(goals, -1)
            if solution:
                return solution
        
        if len(graphplan.graph.levels) >= 2 and graphplan.check_leveloff():
            return None


def have_cake_and_eat_cake_too_graphplan():
    """Solves the cake problem using GraphPlan"""

    pddl = have_cake_and_eat_cake_too()
    graphplan = GraphPlan(pddl)

    def goal_test(kb, goals):
        return all(kb.ask(q) is not False for q in goals)

    goals = [expr('Have(Cake)'), expr('Eaten(Cake)')]

    while True:
        graphplan.graph.expand_graph()
        if (goal_test(graphplan.graph.levels[-1].kb, goals) and graphplan.graph.non_mutex_goals(goals, -1)):
            solution = graphplan.extract_solution(goals, -1)
            if solution:
                return [solution[1]]

        if len(graphplan.graph.levels) >= 2 and graphplan.check_leveloff():
            return None


def three_block_tower_graphplan():
    """Solves the Sussman Anomaly problem using GraphPlan"""

    pddl = three_block_tower()
    graphplan = GraphPlan(pddl)

    def goal_test(kb, goals):
        return all(kb.ask(q) is not False for q in goals)

    goals = [expr('On(A, B)'), expr('On(B, C)')]

    while True:
        if (goal_test(graphplan.graph.levels[-1].kb, goals) and graphplan.graph.non_mutex_goals(goals, -1)):
            solution = graphplan.extract_solution(goals, -1)
            if solution:
                return solution

        graphplan.graph.expand_graph()
        if len(graphplan.graph.levels) >= 2 and graphplan.check_leveloff():
            return None


def air_cargo_graphplan():
    """Solves the air cargo problem using GraphPlan"""

    pddl = air_cargo()
    graphplan = GraphPlan(pddl)

    def goal_test(kb, goals):
        return all(kb.ask(q) is not False for q in goals)

    goals = [expr('At(C1, JFK)'), expr('At(C2, SFO)')]

    while True:
        if (goal_test(graphplan.graph.levels[-1].kb, goals) and graphplan.graph.non_mutex_goals(goals, -1)):
            solution = graphplan.extract_solution(goals, -1)
            if solution:
                return solution

        graphplan.graph.expand_graph()
        if len(graphplan.graph.levels) >= 2 and graphplan.check_leveloff():
            return None


def shopping_graphplan():
    pddl = shopping_problem()
    graphplan = GraphPlan(pddl)

    def goal_test(kb, goals):
        return all(kb.ask(q) is not False for q in goals)

    goals = [expr('Have(Milk)'), expr('Have(Banana)'), expr('Have(Drill)')]

    while True:
        if (goal_test(graphplan.graph.levels[-1].kb, goals) and graphplan.graph.non_mutex_goals(goals, -1)):
            solution = graphplan.extract_solution(goals, -1)
            if solution:
                return solution

        graphplan.graph.expand_graph()
        if len(graphplan.graph.levels) >= 2 and graphplan.check_leveloff():
            return None


def refine_solution(solution):
    """Converts a level-ordered solution into a linear solution"""

    linear_solution = []
    for section in solution[0]:
        for operation in section:
            if not (operation.op[0] == 'P' and operation.op[1].isupper()):
                linear_solution.append(operation)

    return linear_solution


def double_tennis_problem():
    init = [expr('At(A, LeftBaseLine)'),
            expr('At(B, RightNet)'),
            expr('Approaching(Ball, RightBaseLine)'),
            expr('Partner(A, B)'),
            expr('Partner(B, A)')]

    def goal_test(kb):
        required = [expr('Returned(Ball)'), expr('At(a, LeftNet)'), expr('At(a, RightNet)')]
        return all(kb.ask(q) is not False for q in required)

    # Actions

    # Hit
    precond_pos = [expr("Approaching(Ball,loc)"), expr("At(actor,loc)")]
    precond_neg = []
    effect_add = [expr("Returned(Ball)")]
    effect_rem = []
    hit = Action(expr("Hit(actor, Ball, loc)"), [precond_pos, precond_neg], [effect_add, effect_rem])

    # Go
    precond_pos = [expr("At(actor, loc)")]
    precond_neg = []
    effect_add = [expr("At(actor, to)")]
    effect_rem = [expr("At(actor, loc)")]
    go = Action(expr("Go(actor, to, loc)"), [precond_pos, precond_neg], [effect_add, effect_rem])

    return PDDL(init, [hit, go], goal_test)


class HLA(Action):
    """
    Define Actions for the real-world (that may be refined further), and satisfy resource
    constraints.
    """
    unique_group = 1

    def __init__(self, action, precond=None, effect=None, duration=0,
                 consume=None, use=None):
        """
        As opposed to actions, to define HLA, we have added constraints.
        duration holds the amount of time required to execute the task
        consumes holds a dictionary representing the resources the task consumes
        uses holds a dictionary representing the resources the task uses
        """
        precond = precond or [None, None]
        effect = effect or [None, None]
        super().__init__(action, precond, effect)
        self.duration = duration
        self.consumes = consume or {}
        self.uses = use or {}
        self.completed = False
        # self.priority = -1 #  must be assigned in relation to other HLAs
        # self.job_group = -1 #  must be assigned in relation to other HLAs

    def do_action(self, job_order, available_resources, kb, args):
        """
        An HLA based version of act - along with knowledge base updation, it handles
        resource checks, and ensures the actions are executed in the correct order.
        """
        # print(self.name)
        if not self.has_usable_resource(available_resources):
            raise Exception('Not enough usable resources to execute {}'.format(self.name))
        if not self.has_consumable_resource(available_resources):
            raise Exception('Not enough consumable resources to execute {}'.format(self.name))
        if not self.inorder(job_order):
            raise Exception("Can't execute {} - execute prerequisite actions first".
                            format(self.name))
        super().act(kb, args)  # update knowledge base
        for resource in self.consumes:  # remove consumed resources
            available_resources[resource] -= self.consumes[resource]
        self.completed = True  # set the task status to complete

    def has_consumable_resource(self, available_resources):
        """
        Ensure there are enough consumable resources for this action to execute.
        """
        for resource in self.consumes:
            if available_resources.get(resource) is None:
                return False
            if available_resources[resource] < self.consumes[resource]:
                return False
        return True

    def has_usable_resource(self, available_resources):
        """
        Ensure there are enough usable resources for this action to execute.
        """
        for resource in self.uses:
            if available_resources.get(resource) is None:
                return False
            if available_resources[resource] < self.uses[resource]:
                return False
        return True

    def inorder(self, job_order):
        """
        Ensure that all the jobs that had to be executed before the current one have been
        successfully executed.
        """
        for jobs in job_order:
            if self in jobs:
                for job in jobs:
                    if job is self:
                        return True
                    if not job.completed:
                        return False
        return True


class Problem(PDDL):
    """
    Define real-world problems by aggregating resources as numerical quantities instead of
    named entities.

    This class is identical to PDLL, except that it overloads the act function to handle
    resource and ordering conditions imposed by HLA as opposed to Action.
    """
    def __init__(self, initial_state, actions, goal_test, jobs=None, resources=None):
        super().__init__(initial_state, actions, goal_test)
        self.jobs = jobs
        self.resources = resources or {}

    def act(self, action):
        """
        Performs the HLA given as argument.

        Note that this is different from the superclass action - where the parameter was an
        Expression. For real world problems, an Expr object isn't enough to capture all the
        detail required for executing the action - resources, preconditions, etc need to be
        checked for too.
        """
        args = action.args
        list_action = first(a for a in self.actions if a.name == action.name)
        if list_action is None:
            raise Exception("Action '{}' not found".format(action.name))
        list_action.do_action(self.jobs, self.resources, self.kb, args)

    def refinements(hla, state, library):  # TODO - refinements may be (multiple) HLA themselves ...
        """
        state is a Problem, containing the current state kb
        library is a dictionary containing details for every possible refinement. eg:
        {
        "HLA": [
            "Go(Home,SFO)",
            "Go(Home,SFO)",
            "Drive(Home, SFOLongTermParking)",
            "Shuttle(SFOLongTermParking, SFO)",
            "Taxi(Home, SFO)"
               ],
        "steps": [
            ["Drive(Home, SFOLongTermParking)", "Shuttle(SFOLongTermParking, SFO)"],
            ["Taxi(Home, SFO)"],
            [], # empty refinements ie primitive action
            [],
            []
               ],
        "precond_pos": [
            ["At(Home), Have(Car)"],
            ["At(Home)"],
            ["At(Home)", "Have(Car)"]
            ["At(SFOLongTermParking)"]
            ["At(Home)"]
                       ],
        "precond_neg": [[],[],[],[],[]],
        "effect_pos": [
            ["At(SFO)"],
            ["At(SFO)"],
            ["At(SFOLongTermParking)"],
            ["At(SFO)"],
            ["At(SFO)"]
                      ],
        "effect_neg": [
            ["At(Home)"],
            ["At(Home)"],
            ["At(Home)"],
            ["At(SFOLongTermParking)"],
            ["At(Home)"]
                      ]
        }
        """
        e = Expr(hla.name, hla.args)
        indices = [i for i, x in enumerate(library["HLA"]) if expr(x).op == hla.name]
        for i in indices:
            action = HLA(expr(library["steps"][i][0]), [  # TODO multiple refinements
                    [expr(x) for x in library["precond_pos"][i]],
                    [expr(x) for x in library["precond_neg"][i]]
                ],
                [
                    [expr(x) for x in library["effect_pos"][i]],
                    [expr(x) for x in library["effect_neg"][i]]
                ])
            if action.check_precond(state.kb, action.args):
                yield action

    def hierarchical_search(problem, hierarchy):
        """
        [Figure 11.5] 'Hierarchical Search, a Breadth First Search implementation of Hierarchical
        Forward Planning Search'
        The problem is a real-world problem defined by the problem class, and the hierarchy is
        a dictionary of HLA - refinements (see refinements generator for details)
        """
        act = Node(problem.actions[0])
        frontier = deque()
        frontier.append(act)
        while True:
            if not frontier:
                return None
            plan = frontier.popleft()
            print(plan.state.name)
            hla = plan.state  # first_or_null(plan)
            prefix = None
            if plan.parent:
                prefix = plan.parent.state.action  # prefix, suffix = subseq(plan.state, hla)
            outcome = Problem.result(problem, prefix)
            if hla is None:
                if outcome.goal_test():
                    return plan.path()
            else:
                print("else")
                for sequence in Problem.refinements(hla, outcome, hierarchy):
                    print("...")
                    frontier.append(Node(plan.state, plan.parent, sequence))

    def result(problem, action):
        """The outcome of applying an action to the current problem"""
        if action is not None:
            problem.act(action)
            return problem
        else:
            return problem


def job_shop_problem():
    """
    [figure 11.1] JOB-SHOP-PROBLEM

    A job-shop scheduling problem for assembling two cars,
    with resource and ordering constraints.

    Example:
    >>> from planning import *
    >>> p = job_shop_problem()
    >>> p.goal_test()
    False
    >>> p.act(p.jobs[1][0])
    >>> p.act(p.jobs[1][1])
    >>> p.act(p.jobs[1][2])
    >>> p.act(p.jobs[0][0])
    >>> p.act(p.jobs[0][1])
    >>> p.goal_test()
    False
    >>> p.act(p.jobs[0][2])
    >>> p.goal_test()
    True
    >>>
    """
    init = [expr('Car(C1)'),
            expr('Car(C2)'),
            expr('Wheels(W1)'),
            expr('Wheels(W2)'),
            expr('Engine(E2)'),
            expr('Engine(E2)')]

    def goal_test(kb):
        # print(kb.clauses)
        required = [expr('Has(C1, W1)'), expr('Has(C1, E1)'), expr('Inspected(C1)'),
                    expr('Has(C2, W2)'), expr('Has(C2, E2)'), expr('Inspected(C2)')]
        for q in required:
            # print(q)
            # print(kb.ask(q))
            if kb.ask(q) is False:
                return False
        return True

    resources = {'EngineHoists': 1, 'WheelStations': 2, 'Inspectors': 2, 'LugNuts': 500}

    # AddEngine1
    precond_pos = []
    precond_neg = [expr("Has(C1,E1)")]
    effect_add = [expr("Has(C1,E1)")]
    effect_rem = []
    add_engine1 = HLA(expr("AddEngine1"),
                      [precond_pos, precond_neg], [effect_add, effect_rem],
                      duration=30, use={'EngineHoists': 1})

    # AddEngine2
    precond_pos = []
    precond_neg = [expr("Has(C2,E2)")]
    effect_add = [expr("Has(C2,E2)")]
    effect_rem = []
    add_engine2 = HLA(expr("AddEngine2"),
                      [precond_pos, precond_neg], [effect_add, effect_rem],
                      duration=60, use={'EngineHoists': 1})

    # AddWheels1
    precond_pos = []
    precond_neg = [expr("Has(C1,W1)")]
    effect_add = [expr("Has(C1,W1)")]
    effect_rem = []
    add_wheels1 = HLA(expr("AddWheels1"),
                      [precond_pos, precond_neg], [effect_add, effect_rem],
                      duration=30, consume={'LugNuts': 20}, use={'WheelStations': 1})

    # AddWheels2
    precond_pos = []
    precond_neg = [expr("Has(C2,W2)")]
    effect_add = [expr("Has(C2,W2)")]
    effect_rem = []
    add_wheels2 = HLA(expr("AddWheels2"),
                      [precond_pos, precond_neg], [effect_add, effect_rem],
                      duration=15, consume={'LugNuts': 20}, use={'WheelStations': 1})

    # Inspect1
    precond_pos = []
    precond_neg = [expr("Inspected(C1)")]
    effect_add = [expr("Inspected(C1)")]
    effect_rem = []
    inspect1 = HLA(expr("Inspect1"),
                   [precond_pos, precond_neg], [effect_add, effect_rem],
                   duration=10, use={'Inspectors': 1})

    # Inspect2
    precond_pos = []
    precond_neg = [expr("Inspected(C2)")]
    effect_add = [expr("Inspected(C2)")]
    effect_rem = []
    inspect2 = HLA(expr("Inspect2"),
                   [precond_pos, precond_neg], [effect_add, effect_rem],
                   duration=10, use={'Inspectors': 1})

    job_group1 = [add_engine1, add_wheels1, inspect1]
    job_group2 = [add_engine2, add_wheels2, inspect2]

    return Problem(init, [add_engine1, add_engine2, add_wheels1, add_wheels2, inspect1, inspect2],
                   goal_test, [job_group1, job_group2], resources)


