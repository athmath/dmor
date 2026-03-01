from orlab import Model

T = 4
demand = {1: 5, 2: 8, 3: 4, 4: 6}
h = 1
c = 2
I0 = 3

m = Model()

m.add_set("T", range(1, T+1))

m.add_parameter("d", demand, index="T")
m.add_parameter("h", h)
m.add_parameter("c", c)

m.add_variable("x", index="T")
m.add_variable("I", index="T")

def balance(m, t):
    if t == 1:
        return m.I[t] == I0 + m.x[t] - m.d[t]
    return m.I[t] == m.I[t-1] + m.x[t] - m.d[t]

m.add_constraint("balance", balance, index="T")

def obj(m):
    return sum(m.c * m.x[t] + m.h * m.I[t] for t in m.T)

m.set_objective(obj, sense="min")

m.solve()
m.display()