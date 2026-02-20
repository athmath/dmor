import pyomo.environ as pyo
from orlab.solver import solve, display_solution

# Create model
model = pyo.ConcreteModel()

model.x = pyo.Var(domain=pyo.NonNegativeReals)

model.obj = pyo.Objective(
    expr=2 * model.x,
    sense=pyo.maximize
)

model.c = pyo.Constraint(
    expr=model.x <= 5
)

# Solve
solve(model)

# Display
display_solution(model)
