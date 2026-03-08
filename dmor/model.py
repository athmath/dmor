import pyomo.environ as pyo


class Model:
    """
    Algebraic modeling wrapper over Pyomo.

    Students interact only with this class.
    Pyomo is completely hidden internally.
    """

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self):
        self._model = pyo.ConcreteModel()
        self._sets = {}
        self._params = {}
        self._vars = {}
        self._constraints = {}
        self._objective_defined = False

    # ======================================================
    # INTERNAL HELPER
    # ======================================================

    def _register_component(self, name, component, store):
        setattr(self._model, name, component)
        store[name] = component

    # ======================================================
    # SETS
    # ======================================================

    def add_set(self, name, elements):
        s = pyo.Set(initialize=list(elements))
        self._register_component(name, s, self._sets)

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

        self._register_component(name, p, self._params)

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

        self._register_component(name, v, self._vars)

    # ======================================================
    # CONSTRAINTS
    # ======================================================

    def add_constraint(self, name, rule, index=None):

        # allow algebraic expressions for scalar constraints
        if not callable(rule):

            if index is not None:
                raise ValueError(
                    "Indexed constraints must be defined using a rule function."
                )

            expr = rule

            def rule(m):
                return expr

        if index is None:

            c = pyo.Constraint(rule=rule)

        else:

            if isinstance(index, str):
                index = (index,)

            sets = tuple(self._sets[i] for i in index)

            c = pyo.Constraint(*sets, rule=rule)

        self._register_component(name, c, self._constraints)

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

        # allow algebraic expressions
        if not callable(rule):

            expr = rule

            def rule(m):
                return expr

        self._model.obj = pyo.Objective(rule=rule, sense=s)

        self._objective_defined = True

    # ======================================================
    # STATISTICS
    # ======================================================

    def _model_stats(self):

        nvars = sum(len(v) if v.is_indexed() else 1 for v in self._vars.values())

        ncons = sum(len(c) if c.is_indexed() else 1 for c in self._constraints.values())

        print("\nModel statistics")
        print("-" * 30)
        print("Sets:", len(self._sets))
        print("Parameters:", len(self._params))
        print("Variables:", nvars)
        print("Constraints:", ncons)

    
    # ======================================================
    # SOLVE
    # ======================================================

    def solve(self, solver="appsi_highs", tee=False):

        if tee: 
            self._model_stats()
        
        if not hasattr(self._model, "dual"):
            self._model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

        opt = pyo.SolverFactory(solver)

        if not opt.available():
            raise RuntimeError(
                f"Solver '{solver}' is not available. Check that highspy is installed."
            )

        results = opt.solve(self._model, tee=tee)

        status = results.solver.status
        condition = results.solver.termination_condition

        if status != pyo.SolverStatus.ok or condition != pyo.TerminationCondition.optimal:

            print("\nSolver status:", status)
            print("Termination condition:", condition)

            if condition == pyo.TerminationCondition.infeasible:
                print("Model appears to be infeasible.")

            elif condition == pyo.TerminationCondition.unbounded:
                print("Model appears to be unbounded.")

            raise RuntimeError("Optimization failed.")

        if tee:
            print("\nSolver termination:", condition)

        return results

    # ======================================================
    # DISPLAY
    # ======================================================

    def display(self):

        print("\nOptimal Solution")
        print("-" * 30)

        for name, var in self._vars.items():

            if var.is_indexed():

                print(f"\n{name}")

                for idx in sorted(var):
                    val = pyo.value(var[idx])
                    print(f"  {idx}: {val:.4f}")

            else:

                val = pyo.value(var)
                print(f"{name} = {val:.4f}")

        print("\n" + "-" * 30)
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
    # SUM HELPER
    # ======================================================

    def sum(self, expr):
        return pyo.quicksum(expr)

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
