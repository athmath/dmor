import numpy as np
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

    def add_variable(self, name, index=None, lb=None, ub=None, domain="nonneg"):

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
    # MATRIX CONSTRAINTS
    # ======================================================

    def add_matrix_constraints(
    self,
    A,
    varname,
    b,
    sense="==",
    name="matrix_con",
    row_index=None
    ):

        import numpy as np

        if varname not in self._vars:
            raise ValueError(f"Variable '{varname}' not defined.")

        x = self._vars[varname]

        # --------------------------------------------
        # DENSE CASE
        # --------------------------------------------
        if isinstance(A, np.ndarray):

            m_rows, n_cols = A.shape
            b = np.array(b).flatten()

            if len(b) != m_rows:
                raise ValueError("Dimension mismatch between A and b")

            # ----------------------------------------
            # GET VARIABLE INDEX SET (CRITICAL FIX)
            # ----------------------------------------
            var_index_set = list(x.index_set())

            if len(var_index_set) != n_cols:
                raise ValueError(
                    "Number of columns in A must match size of variable index set"
                )

            # ----------------------------------------
            # ROW SET
            # ----------------------------------------
            if row_index is None:
                row_index = f"{name}_rows"
                self.add_set(row_index, range(m_rows))

            rowset = list(self._sets[row_index])

            if len(rowset) != m_rows:
                raise ValueError("Row index set size must match number of rows in A")

            # ----------------------------------------
            # RULE
            # ----------------------------------------
            def rule(model, i):

                i0 = rowset.index(i)

                expr = sum(
                    A[i0, j] * x[var_index_set[j]]
                    for j in range(n_cols)
                )

                if sense == "==":
                    return expr == b[i0]
                elif sense == "<=":
                    return expr <= b[i0]
                elif sense == ">=":
                    return expr >= b[i0]
                else:
                    raise ValueError("sense must be '==', '<=', '>='")

            self.add_constraint(name, rule, index=row_index)

        # --------------------------------------------
        # SPARSE CASE
        # --------------------------------------------
        elif isinstance(A, dict):

            rows = sorted({i for (i, j) in A})

            if row_index is None:
                row_index = f"{name}_rows"
                self.add_set(row_index, rows)

            row_cols = {i: [] for i in rows}
            for (i, j) in A:
                row_cols[i].append(j)

            if isinstance(b, dict):
                b_dict = b
            else:
                b_dict = {i: b[k] for k, i in enumerate(rows)}

            def rule(model, i):

                expr = sum(A[i, j] * x[j] for j in row_cols[i])

                if sense == "==":
                    return expr == b_dict[i]
                elif sense == "<=":
                    return expr <= b_dict[i]
                elif sense == ">=":
                    return expr >= b_dict[i]
                else:
                    raise ValueError("sense must be '==', '<=', '>='")

            self.add_constraint(name, rule, index=row_index)

        else:
            raise TypeError("A must be dict or numpy.ndarray")

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

    # ======================================================
    # MODEL INTROSPECTION
    # ======================================================

    def constraints_list(self):
        """
        Return a list of all constraints as strings.
        Each indexed constraint is expanded.
        """
        result = []

        for c in self._model.component_objects(pyo.Constraint, active=True):
            for idx in c:
                expr = c[idx].expr
                result.append(str(expr))

        return result

    def objective_expression(self):
        """
        Return the objective function as a string.
        Assumes a single active objective.
        """
        obj = next(self._model.component_data_objects(pyo.Objective, active=True))
        return str(obj.expr)
    

    # ======================================================
    # EXTRACTING SOLUTION VALUES
    # ======================================================


    def get_values(self, name):
        """
        Return variable values as a NumPy array.
        Assumes ordered (sortable) indices.
        """
        var = getattr(self._model, name)

        # Scalar variable
        if not var.is_indexed():
            return np.array([pyo.value(var)])

        # Indexed variable
        keys = list(var.keys())
        keys_sorted = sorted(keys)

        return np.array([pyo.value(var[k]) for k in keys_sorted])