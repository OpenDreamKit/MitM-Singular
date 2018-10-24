from openmath import openmath as om, helpers

# the head for evaluating an expression
EVAL_SYM = om.OMSymbol(name="MitM_Evaluate", cd="scscp_transient_1") # cdbase will be ignored

# helpers for building OpenMath objects
CDBASE = helpers.CDBaseHelper("https://www.singular.uni-kl.de/")
SINGULAR = CDBASE.singular

Groeber = SINGULAR.groebner         # Groebner base of an ideal, takes and returns ideal
Ideal = SINGULAR.ideal              # takes polynomials, returns ideal

polyd1 = SINGULAR.polyd1
poly_ring = polyd1.poly_ring_d_named # takes a ring and variable names, returns polynomial ring
dmp = polyd1.DMP                     # takes a polynomial ring and a polynomial (SDMP) 
sdmp = polyd1.SDMP                   # takes monomials, returns polynomial, no info about ring
term = polyd1.term                   # takes coefficient and exponents, returns monomial, no info about variable names

int_ring_sym = om.OMSymbol("integers", "ring3") # ring of integers

# the corresponding om.OMSymbol objects
poly_ring_sym = poly_ring.toOM()
dmp_sym = dmp.toOM() 
sdmp_sym = sdmp.toOM()
term_sym = term.toOM()
