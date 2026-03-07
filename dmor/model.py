from xml import dom

import pyomo.environ as pyo


class Model:
    """
    Algebraic modeling wrapper over Pyomo.

    Students interact only with this class.
    Pyomo is completely hidden internally.
    """

    def __init__(self):
        self._model = pyo.ConcreteModel()
        self._sets = {}
        self._params = {}
        self._vars = {}
        self._constraints = {}
        self._objective_defined = False

    # ======================================================
    # SETS
    # ======================================================

    def add_set(self, name, elements):
        s = pyo.Set(initialize=list(elements))
        setattr(self._model, name, s)
        self._sets[name] = s

    # ======================================================
    # PARAMETERS
    # ======================================================

    def add_parameter(self, name, values, index=None):
        if index is None:
            p = pyo.Param(initialize=values)
        else:
            if isinstance(index, str):
                index = (index,)
            sets = tuple(self._sets[i] for i in index)
            p = pyo.Param(*sets, initialize=values)

        setattr(self._model, name, p)
        self._params[name] = p

    # ======================================================
    # VARIABLES
    # ======================================================

    def add_variable(self, name, index=None, lb=0, domain="nonneg"):

        if domain == "nonneg":
            dom = pyo.NonNegativeReals
        elif domain == "real":
            dom = pyo.Reals
        elif domain == "binary":
            dom = pyo.Binary
        elif domain == "integer":
            dom = pyo.Integers
        else:
            raise ValueError("Unknown domain")

        if index is None:
            if lb is not None:
                v = pyo.Var(domain=dom, bounds=(lb, None))
            else:
                v = pyo.Var(domain=dom)
        else:
            if isinstance(index, str):
                index = (index,)
            sets = tuple(self._sets[i] for i in index)
            if lb is not None:
                v = pyo.Var(*sets, domain=dom, bounds=(lb, None))
            else:
                v = pyo.Var(*sets, domain=dom)

        setattr(self._model, name, v)
        self._vars[name] = v

    # ======================================================
    # CONSTRAINTS
    # ======================================================

    def add_constraint(self, name, rule, index=None):
        if index is None:
            c = pyo.Constraint(rule=rule)
        else:
            if isinstance(index, str):
                index = (index,)
            sets = tuple(self._sets[i] for i in index)
            c = pyo.Constraint(*sets, rule=rule)

        setattr(self._model, name, c)
        self._constraints[name] = c

    # ======================================================
    # OBJECTIVE
    # ======================================================

    def set_objective(self, rule, sense="min"):
        if self._objective_defined:
            raise ValueError("Objective already defined")

        if sense == "min":
            s = pyo.minimize
        elif sense == "max":
            s = pyo.maximize
        else:
            raise ValueError("sense must be 'min' or 'max'")

        self._model.obj = pyo.Objective(rule=rule, sense=s)
        self._objective_defined = True

    # ======================================================
    # SOLVE
    # ======================================================

    def solve(self, solver="highs", tee=False):

    # attach suffix for dual values
    if not hasattr(self._model, "dual"):
        self._model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

    opt = pyo.SolverFactory(solver)

    if not opt.available():
        raise RuntimeError(
            f"Solver '{solver}' is not available. "
            "Check that highspy is installed."
        )

    results = opt.solve(self._model, tee=tee)

    # check solver status
    if results.solver.status != pyo.SolverStatus.ok:
        raise RuntimeError(f"Solver status: {results.solver.status}")

    if results.solver.termination_condition != pyo.TerminationCondition.optimal:
        raise RuntimeError(
            f"Optimization failed: {results.solver.termination_condition}"
        )

    if tee:
        print("\nSolver termination:", results.solver.termination_condition)
    
    return results

    # ======================================================
    # DISPLAY
    # ======================================================

    def display(self):
        print("\nOptimal Solution")
        print("-" * 30)

        for name, var in self._vars.items():
            if var.is_indexed():
                for idx in var:
                    print(f"{name}[{idx}] = {pyo.value(var[idx]):.4f}")
            else:
                print(f"{name} = {pyo.value(var):.4f}")

        print("-" * 30)
        print("Objective =", pyo.value(self._model.obj))

    # ======================================================
    # SHADOW PRICES
    # ======================================================

    def shadow_prices(self):
        print("\nShadow Prices")
        print("-" * 30)

        for cname, c in self._constraints.items():
            if c.is_indexed():
                for idx in c:
                    dual = self._model.dual.get(c[idx], None)
                    print(f"{cname}[{idx}] = {dual}")
            else:
                dual = self._model.dual.get(c, None)
                print(f"{cname} = {dual}")

    # ======================================================
    # SLACKS
    # ======================================================

    def slacks(self, tol=1e-6):
        print("\nConstraint Slacks")
        print("-" * 30)

        for cname, c in self._constraints.items():
            if c.is_indexed():
                for idx in c:
                    slack = c[idx].slack()
                    status = "binding" if abs(slack) < tol else ""
                    print(f"{cname}[{idx}] = {slack:.4f} {status}")
            else:
                slack = c.slack()
                status = "binding" if abs(slack) < tol else ""
                print(f"{cname} = {slack:.4f} {status}")    

    # ======================================================
    # ATTRIBUTE ACCESS FOR RULES
    # ======================================================

    def __getattr__(self, name):
        """
        Allows students to write m.x, m.T, m.d inside rules
        """
        if hasattr(self._model, name):
            return getattr(self._model, name)
        raise AttributeError(name)
