import pytest
from dmor.model import Model

def test_simple_lp_solution():

    m = Model()

    # Variables
    m.add_variable("x1", lb=0)
    m.add_variable("x2", lb=0)

    # Objective
    def obj_rule(model):
        return 3 * model.x1 + 5 * model.x2

    m.set_objective(rule=obj_rule, sense="max")

    # Constraints
    def c1_rule(model):
        return 5 * model.x1 + model.x2 <= 20

    def c2_rule(model):
        return model.x1 + 4 * model.x2 <= 18

    m.add_constraint("c1", rule=c1_rule)
    m.add_constraint("c2", rule=c2_rule)

    # Solve
    m.solve()

    # Check solution
    x1 = m.x1.value
    x2 = m.x2.value

    assert abs(x1 - 62/19) < 1e-6
    assert abs(x2 - 70/19) < 1e-6