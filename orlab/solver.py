import pyomo.environ as pyo


def solve(model, solver="glpk", tee=False):
    """
    Solve a Pyomo model.

    Parameters
    ----------
    model : Pyomo model
    solver : str
        Solver name (default: glpk)
    tee : bool
        If True, show solver output
    """
    opt = pyo.SolverFactory(solver)
    results = opt.solve(model, tee=tee)
    return results


def display_solution(model):
    """
    Print variable values and objective value.
    """
    print("\nOptimal Solution")
    print("-" * 20)

    # Print all variables
    for var in model.component_objects(pyo.Var, active=True):
        for index in var:
            print(f"{var.name}{index} = {pyo.value(var[index]):.4f}")

    print("-" * 20)

    # Print objective value
    for obj in model.component_objects(pyo.Objective, active=True):
        print(f"Objective = {pyo.value(obj):.4f}")
