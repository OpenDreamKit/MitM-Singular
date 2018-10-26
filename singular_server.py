#
# Hackserver to provide Singular over SCSCP
#
import os

import socket
import socketserver
import logging
from openmath import openmath as om, convert as conv

from scscp.client import TimeoutError, CONNECTED
from scscp.server import SCSCPServer
from scscp.scscp import SCSCPQuit, SCSCPProtocolError
from scscp import scscp

import PySingular as sing

import poly_parsing as parse
from names import *

import traceback
from termcolor import colored


def RunSingularCommand(cmd):
    print(colored("Running command: " + cmd, "green"))
    return sing.RunSingularCommand(cmd)

def makename():
    name = ""
    no = makename.var_counter
    while no > 0:
        remainder = no % 26
        no = no // 26
        name += chr(97 + remainder)
    makename.var_counter += 1
    return name
makename.var_counter = 1

def retrieve_poly(name):
    output = RunSingularCommand(name + ";")[1]
    return parse.parse_polynomial(output)

def retrieve_int(name):
    return om.OMInteger(int(RunSingularCommand(name + ";")[1][:-1]))

def retrieve_ideal(name):
    output = RunSingularCommand(name + ";")[1]
    poly_lines = output.splitlines()
    polys = []
    for poly_line in poly_lines:
        print(colored(poly_line.split("=")[1], "yellow"))
        polys.append(parse.parse_polynomial(poly_line.split("=")[1]))
    return Ideal(polys)

def retrieve(name):
    """takes a Singular-returned string and turns it into OpenMath using the retrieve_XXX methods above"""
    # cut off the final symbol which is newline
    var_type = RunSingularCommand("typeof(" + name + ");")[1][:-1]
    print(colored(var_type, "red"))
    if var_type == "poly":
        return retrieve_poly(name)
    elif var_type == "int":
        return retrieve_int(name)
    elif var_type == "ideal":
        return retrieve_ideal(name)
    else:
        return None

class poly_info:
    def __init__(self, data):
        poly = data
        self.ring = poly.arguments[0]
        self.sdmp = poly.arguments[1]
        self.terms = self.sdmp.arguments
        self.variables = self.ring.arguments[1:]

def getVarName(v):
    return v.string

def ring_ctor(ring_name, variables):
    command = "ring " + ring_name + " = 0, ("
    for v in variables:
        command += getVarName(v)
        command += ","
    command = command[:-1]
    command += "), lp;"
    # initialise the ring
    RunSingularCommand(command)

def poly_ctor(poly_name, terms, ring):
    command = "poly " + poly_name + " = "
    print(colored(str(ring), "blue"))
    for term in terms:
        if term.arguments[0].integer != 1:
            command += str(term.arguments[0].integer)
        for i in range(1, len(ring.arguments)):
            if term.arguments[i].integer != 0:
                command += "*"
                command += getVarName(ring.arguments[i])
                if term.arguments[i].integer != 1:
                    command += "^"
                    command += str(term.arguments[i].integer)
        command += "+"
    # to remove the last plus
    command = command[:-1]
    command += ";"
    RunSingularCommand(command)

def poly_ctor_1(poly_name, terms, varnames):
    command = "poly " + poly_name + " = "
    for term in terms:
        for i in range(0, len(varnames)):
            command += str(term.arguments[i].integer)
            command += varnames[i]
        command += str(term.arguments[-1].integer)
        command += "+"
    command = command[:-1]
    command += ";"
    RunSingularCommand(command)

def poly_eq(name, data):
    if (len(data) != 2):
        raise TypeError
    poly1 = poly_info(data[0])
    poly2 = poly_info(data[1])

    # only support integer ring for coefficients for now
    if poly1.ring.arguments[0] != parse.int_ring_sym:
        raise TypeError

    variables = []
    for v in poly1.variables:
        variables.append(v)
    for v in poly2.variables:
        if v not in variables:
            variables.append(v)

    ring_ctor("r", variables)
    poly_ctor("p1", poly1.terms, poly1.ring)
    poly_ctor("p2", poly2.terms, poly2.ring)

    RunSingularCommand("int " + name + " = p1 == p2;")[1]

def polynomial(name, data):
    poly = poly_info(data[0])

    ring_ctor("r", poly.variables)
    poly_ctor(name, poly.terms, poly.ring)

def ideal(name, data):
    poly = poly_info(data)
    ring_ctor("r", poly.variables)
    poly_ctor("p", poly.terms, poly.ring)

    RunSingularCommand("ideal " + name + " = ideal(p)")

def groebner(name, data):
    polys = []
    data = data[0]
    variables = []
    for poly_data in data.arguments:
        polys.append(poly_info(poly_data))
        for v in poly_info(poly_data).variables:
            if v not in variables:
                variables.append(v)
    ring_ctor("r", variables)

    arg_str = ""
    for i in range(0, len(polys)):
        s = "p" + str(i)
        poly_ctor(s, polys[i].terms, polys[i].ring)
        arg_str += s
        arg_str += ","
    arg_str = arg_str[:-1]
    ideal_name = makename()

    sing.RunSingularCommand("ideal " + ideal_name + " = " + arg_str + ";")
    sing.RunSingularCommand("ideal " + name + " = groebner(" + ideal_name + ");")

def dimension(data):
    poly = poly_info(data)
    ring_ctor("r", poly.variables)
    poly_ctor("p", poly.terms, poly.ring)

    RunSingularCommand("int " + name + " = dim(p)")

# Supported functions
CD_SCSCP2 = ['get_service_description', 'get_allowed_heads', 'is_allowed_head', 'get_signature']
CD_SINGULAR = ['polynomial_eq', 'polynomial', 'ideal', 'groebner']


def get_handler(head):
    if head == "polynomial_eq":
        return poly_eq
    elif head == "polynomial":
        return polynomial
    elif head == "ideal":
        return ideal
    elif head == "groebner":
        return groebner
    elif head == "dimension":
        return dimension
    else:
        return None

def evaluate(obj):
    """evaluates an expression via Singular"""
    if isinstance(obj, om.OMApplication):
        fun = obj.elem
        # check for OMA(OMS(singular, head), args), cdbase is ignored
        if isinstance(fun, om.OMSymbol) and fun.cd == SINGULAR._cd:
            head = fun.name 
            handler = get_handler(head)
            if handler != None:
                args = obj.arguments
                name = makename()
                handler(name, args)
                return retrieve(name)
    return obj


# the boilerplate for SCSCP server that wraps around the evaluate function
class SCSCPRequestHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.server.log.info("New connection from %s:%d" % self.client_address)
        self.log = self.server.log.getChild(self.client_address[0])
        self.scscp = SCSCPServer(self.request, self.server.name,
                                     self.server.version, logger=self.log)

    def handle(self):
        self.scscp.accept()
        while True:
            try:
                call = self.scscp.wait()
            except TimeoutError:
                continue
            except SCSCPQuit as e:
                self.log.info(e)
                break
            except ConnectionResetError:
                self.log.info('Client closed unexpectedly.')
                break
            except SCSCPProtocolError as e:
                self.log.info('SCSCP protocol error: %s.' % str(e))
                self.log.info('Closing connection.')
                self.scscp.quit()
                break
            self.handle_call(call)

    def handle_call(self, call):
        if (call.type != 'procedure_call'):
            raise SCSCPProtocolError('Bad message from client: %s.' % call.type, om=call.om())
        try:
            head = call.data.elem.name
            args = call.data.arguments
            self.log.debug('Requested head: %s...' % head)

            if call.data.elem.cd == 'scscp2' and head in CD_SCSCP2:
                res = getattr(self, head)(call.data)
            elif call.data.elem.cd == EVAL_SYM.cd and head == EVAL_SYM.name and len(args) == 1:
                #args = [conv.to_python(a) for a in call.data.arguments]
                res = evaluate(args[0])
            else:
                self.log.debug('...head unknown.')
                return self.scscp.terminated(call.id, om.OMError(
                    om.OMSymbol('unhandled_symbol', cd='error'), [call.data.elem]))

            strlog = str(res)
            print(colored(strlog, "green"))
            self.log.debug('...sending result: %s' % (strlog[:20] + (len(strlog) > 20 and '...')))
            return self.scscp.completed(call.id, res)
        except (AttributeError, IndexError, TypeError) as e:
            traceback.print_exc()
            self.log.debug('...client protocol error.')
            return self.scscp.terminated(call.id, om.OMError(
                om.OMSymbol('unexpected_symbol', cd='error'), [call.data]))
        except Exception as e:
            self.log.exception('Unhandled exception:')
            return self.scscp.terminated(call.id, 'system_specific',
                                             'Unhandled exception %s.' % str(e))

    def get_allowed_heads(self, data):
        return scscp.symbol_set([om.OMSymbol(head, cd='scscp2') for head in CD_SCSCP2] + [EVAL_SYM], cdnames=['scscp1'])

    def is_allowed_head(self, data):
        head = data.arguments[0]
        return conv.to_openmath((head.cd == 'scscp_trans_1' and head.name in CD_SCSCP_TRANS)
                                    or (head.cd == 'scscp2' and head.name in CD_SCSCP2)
                                    or (head.cd == EVAL_SYM.cd and head.name == EVAL_SYM.name)
                                    or head.cd == 'scscp1')

    def get_service_description(self, data):
        return scscp.service_description(self.server.name.decode(),
                                             self.server.version.decode(),
                                             self.server.description)

    def get_signature(self, data):
        print(colored(str(data), "blue"))
        if data.arguments[0].name == "groebner":
            sig_sym = om.OMSymbol("signature", "scscp2")
            func_sym = om.OMSymbol("groebner", "singular")
            zero_sym = om.OMInteger(0)
            infinity_sym = om.OMSymbol("infinity", "nums1")
            all_set_sym = om.OMSymbol("symbol_set_all", "scscp2")
            return om.OMApplication(sig_sym, [func_sym, zero_sym, infinity_sym, all_set_sym])
        return om.OMApplication(om.OMSymbol("symbol_set", "scscp2"), [])

class Server(socketserver.ThreadingMixIn, socketserver.TCPServer, object):
    allow_reuse_address = True

    def __init__(self, host='localhost', port=26135,
                     logger=None, name=b'SingularServer', version=b'0.0.1',
                     description='Singular SCSCP Server'):
        super(Server, self).__init__((host, port), SCSCPRequestHandler)
        self.log = logger or logging.getLogger(__name__)
        self.name = name
        self.version = version
        self.description = description

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('singular_server')
    srv = Server(host=os.environ.get('SCSCP_HOST') or 'localhost', logger=logger)

    #sing.InitializeSingular("/usr/bin/Singular")
    sing.InitializeSingular("/usr/bin/Singular")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
        srv.server_close()
