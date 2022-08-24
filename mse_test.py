# from itertools import tee
# from cvxopt.glpk import ilp
# import numpy as np
import math
from cvxopt import matrix

# c = matrix(np.ones(6))

# coeff = np.array(
#     [
#         [1, 2, 0, 0, 3, 0],
#         [1, 1, 0, 0, 0, 1],
#         [0, 0, 1, 1, 0, 0],
#         [0, 0, 1, 1, 1, 0],
#         [0, 0, 0, 1, 1, 1],
#         [0, 1, 0, 0, 1, 1],
#     ],
#     dtype=float,
# )
# G = matrix(-coeff)

# h = matrix(-1 * np.ones(6))

# I = set([0, 1])

# B = set()

# # (status, x) = ilp(c, G, h, matrix(1.0, (0, 6)), matrix(1.0, (0, 1)), I, B)

# print(2 * matrix([[2, 0.5], [0.5, 1]]))

# from cvxopt import matrix, solvers

# Q = matrix([[2, 0.5], [0.5, 1]])
# p = matrix([1.0, 1.0])
# G = matrix([[-1.0, 0.0], [0.0, -1.0]])
# h = matrix([0.0, 0.0])
# A = matrix([1.0, 1.0], (1, 2))
# b = matrix(1.0)
# sol = solvers.qp(Q, p, G, h, A, b)
# print(sol["x"])
# from cvxopt import normal
# from cvxopt.modeling import variable, op, max, sum

# import pylab

# m, n = 5, 10
# A = normal(m, n)
# b = normal(m)

# print(A)

# x1 = variable(n)
# op(max(abs(A * x1 - b))).solve()

# x2 = variable(n)
# op(sum(abs(A * x2 - b))).solve()

# x3 = variable(n)
# op(sum(max(0, abs(A * x3 - b) - 0.75, 2 * abs(A * x3 - b) - 2.25))).solve()

from cvxopt import matrix, solvers
import numpy as np

Q = 2 * matrix(np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype="float"))
p = matrix(np.array([0.0, 0.0, 0.0], dtype="float"))
# G = matrix([[-1.0, 0.0], [0.0, -1.0]])
# h = matrix([0.0, 0.0])
A = matrix(np.array([[1, 2, 8], [2, 3, 7], [3, 5, 3]], dtype="float"), (3, 3))
b = matrix(np.array([5, 6, 8], dtype="float"))
sol = solvers.qp(P=Q, q=p, A=A, b=b)
print(sol)
print(sol["x"])
print(sol["y"])
print(sol["z"])
