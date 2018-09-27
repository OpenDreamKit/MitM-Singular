
# coding: utf-8

# In[ ]:

from openmath import openmath as om
import collections


# In[ ]:

int_ring = om.OMSymbol("integers", "ring3")
sdmp_sym = om.OMSymbol("SDMP", "polyd1")
term_sym = om.OMSymbol("term", "polyd1")
poly_ring_sym = om.OMSymbol("poly_ring_d_named", "polyd1")
dmp_sym = om.OMSymbol("DMP", "polyd1")


# In[ ]:

def tokenise(poly_str):
    poly_str = poly_str.replace(" ", "")
    tokens = collections.deque()
    while len(poly_str) > 0:
        current_token = ""
        if str(poly_str[0]).isalpha():
            while len(poly_str) > 0 and str(poly_str[0]).isalpha():
                current_token = current_token + poly_str[0]
                poly_str = poly_str[1:]
            tokens.append(current_token)
        elif str(poly_str[0]).isnumeric():
            while len(poly_str) > 0 and str(poly_str[0]).isnumeric():
                current_token = current_token + poly_str[0]
                poly_str = poly_str[1:]
            tokens.append(current_token)
        elif poly_str[0] == '+':
            tokens.append("+")
            poly_str = poly_str[1:]
        elif poly_str[0] == "-":
            poly_str = poly_str[1:]
            while len(poly_str) > 0 and str(poly_str[0]).isnumeric():
                current_token = current_token + poly_str[0]
                poly_str = poly_str[1:]
            if current_token == "":
                tokens.append("-1")
            else:
                tokens.append("-" + current_token)
        else:
            # just discard the character otherwise
            poly_str = poly_str[1:]
    return tokens


# In[ ]:

def parse_term(tokens):
    if tokens.__len__() <= 0:
        return None
    term = {}
    token = tokens.popleft()
    try:
        term["index"] = int(token)
    except ValueError:
        term["index"] = 1
        tokens.appendleft(token)
        
    term["var_list"] = set()
    while tokens.__len__() > 0:
        v = tokens.popleft()
        try:
            intgr = int(v)
            if (intgr < 0):
                tokens.appendleft(v)
                break
        except ValueError:
            pass
        if v == "+":
            break
        try:
            token = tokens.popleft()
            exp = int(token)
        except ValueError:
            tokens.appendleft(token)
            exp = 1
        except IndexError:
            exp = 1
        if exp < 0:
            raise Exception
        term[v] = exp
        term["var_list"].add(v)
    return term


# In[ ]:

def parse_polynomial(poly_str):
    try:
        tokens = tokenise(poly_str)
        terms = []
        var_list = set()
        term = parse_term(tokens)
        while term != None:
            terms.append(term)
            var_list = var_list.union(term["var_list"])
            term = parse_term(tokens)
    
        var_list = list(var_list)
        poly_ring = om.OMApplication(poly_ring_sym, [int_ring] + [om.OMVariable(var_name) for var_name in list(var_list)])
        om_terms = []
        for term in terms:
            args = []
            args.append(om.OMInteger(term["index"]))
            for i in range(0, len(var_list)):
                if var_list[i] not in term:
                    args.append(om.OMInteger(0))
                else:
                    args.append(om.OMInteger(term[var_list[i]]))
            om_terms.append(om.OMApplication(term_sym, args))
        sdmp = om.OMApplication(sdmp_sym, om_terms)
        return om.OMApplication(dmp_sym, [poly_ring, sdmp])
    except Exception as e:
        print(e)
        print("Please enter a valid polynomial")
        return None

def poly_to_str(poly):
    poly_str = ""
    for term in poly.arguments[1].arguments:
        if term.arguments[0].integer == 0:
            continue
        if term.arguments[0].integer == 1:
            pass
        elif term.arguments[0].integer == -1:
            poly_str = poly_str + "-"
        else:
            poly_str = poly_str + str(term.arguments[0].integer)
            
        for i in range(1, len(poly.arguments[0].arguments)):
            if term.arguments[i].integer != 0:
                poly_str = poly_str + poly.arguments[0].arguments[i].name
                if term.arguments[i].integer != 1:
                    poly_str = poly_str + str(term.arguments[i].integer)
            if i == len(poly.arguments[0].arguments) - 1:
                poly_str = poly_str + "+"
    poly_str = poly_str[:-1]
    return poly_str
