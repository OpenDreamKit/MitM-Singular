import scscp, lxml.etree as etree
from names import *

def evaluate(obj):
    """evaluate an object via Singular and SCSCP"""
    client = scscp.SCSCPCLI("localhost", 26135)
    return client.heads.scscp_transient_1.MitM_Evaluate.([obj])
    print(obj)

# see 'names.py' for the meaning of the symbols
# i.e., poly_ring, dmp, sdmp, term, Ideal, Groebner

# a polynomial ring
R = poly_ring(int_ring_sym, "x1", "x2", "x3", "x4") # TODO singular_server and poly_parse expect these as (unbound) OMVs

# some polynomials
p1 = dmp(R, sdmp(term(3,1,0,0,0), term(2,0,1,0,0))) # 3*x1+2*x2
p2 = dmp(R, sdmp(term(3,0,1,0,0), term(2,0,0,1,0))) # 3*x2+2*x3

# an ideal
I = Ideal(p1, p2)

G = Groebner(I)

# compute a 
evaluate(G)
