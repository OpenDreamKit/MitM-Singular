from openmath import openmath as om, helpers

# this file defines all OpenMath-affecting names <nd their signature in the Singular interface

# the head for evaluating an expression
EVAL_SYM = om.OMSymbol(name="MitM_Evaluate", cd="scscp_transient_1") # cdbase will be ignored

# an arbitrary cdbase
CDBASE = helpers.CDBaseHelper("https://www.singular.uni-kl.de/")

# cds
SINGULAR = CDBASE.singular
polyd1 = CDBASE.polyd1
ring3 = CDBASE.ring3

# symbols
Groeber = SINGULAR.groebner         # Groebner base of an ideal, takes and returns ideal
Ideal = SINGULAR.ideal              # takes polynomials, returns ideal

poly_ring_sym = polyd1.poly_ring_d_named # takes a ring and variable names, returns polynomial ring
dmp_sym = polyd1.DMP                     # takes a polynomial ring and a polynomial (SDMP) 
sdmp_sym = polyd1.SDMP                   # takes monomials, returns polynomial, no info about ring
term_sym = polyd1.term                   # takes coefficient and exponents, returns monomial, no info about variable names

int_ring_sym = ring3.integers            # the ring of integers
