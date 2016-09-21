import search
from math import(cos, pi)

stl_map = search.UndirectedGraph(dict(
    Kirkwood=dict(Webster=10, Clayton=17, MapleWood=17, Glendale=7),
    St_Louis=dict(Clayton=12),
    Glendale=dict(St_Louis=19),
    MapleWood=dict(St_Louis=11),
    Clayton=dict(Webster=14, St_Louis=12, Kirkwood=17),
    Webster=dict(Kirkwood=10, Clayton=14),
))
stl_map.locations = dict(
    St_Louis=(38.6270, 90.1994),Webster=(38.5926, 90.3573),Kirkwood=(38.5834, 90.4068),
    Glendale=(38.5959, 90.3771), MapleWood=(38.6104, 90.3228), Clayton=(38.6426, 90.3237),
)

stl_puzzle = search.GraphProblem('Kirkwood', 'St_Louis', stl_map)

stl_puzzle.description = '''
An abbreviated map of Sumner County, TN.
This map is unique, to the best of my knowledge.
'''


class LightSwitch(search.Problem):
    def actions(self, state):
        return ['up', 'down']

    def result(self, state, action):
        if action == 'up':
            return 'on'
        else:
            return 'off'

    def goal_test(self, state):
        return state == 'on'

    def h(self, node):
        state = node.state
        if self.goal_test(state):
            return 0
        else:
            return 1

switch_puzzle = LightSwitch('off')
switch_puzzle.label = 'Light Switch'

myPuzzles = [
    stl_puzzle,
    switch_puzzle,
]