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

import traceback
from termcolor import colored

false_sym = om.OMSymbol("false", "logic1")
true_sym = om.OMSymbol("true", "logic1")
int_ring_sym = om.OMSymbol("integers", "ring3")
sdmp_sym = om.OMSymbol("SDMP", "polyd")
term_sym = om.OMSymbol("term", "polyd")
poly_ring_sym = om.OMSymbol("poly_ring_d_named", "polyd")
dmp_sym = om.OMSymbol("DMP", "polyd")
list_sym = om.OMSymbol("list", "list1")

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
    output = sing.RunSingularCommand(name + ";")[1]
    return parse.parse_polynomial(output)

def retrieve_int(name):
    return om.OMInteger(int(sing.RunSingularCommand(name + ";")[1][:-1]))

def retrieve_ideal(name):
    output = sing.RunSingularCommand(name + ";")[1]
    poly_lines = output.splitlines()
    polys = []
    for poly_line in poly_lines:
        print(colored(poly_line.split("=")[1], "yellow"))
        polys.append(parse.parse_polynomial(poly_line.split("=")[1]))
    return om.OMApplication(list_sym, polys)

def retrieve(name):
    # cut off the final symbol which is newline
    var_type = sing.RunSingularCommand("typeof(" + name + ");")[1][:-1]
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

def ring_ctor(ring_name, variables):
    command = "ring " + ring_name + " = 0, ("
    for v in variables:
        command += v.name
        command += ","
    command = command[:-1]
    command += "), lp;"
    # initialise the ring
    sing.RunSingularCommand(command)

def poly_ctor(poly_name, terms, ring):
    command = "poly " + poly_name + " = "
    print(colored(str(ring), "blue"))
    for term in terms:
        for i in range(1, len(ring.arguments)):
            command += str(term.arguments[i-1].integer)
            command += ring.arguments[i].name
        command += str(term.arguments[-1].integer)
        command += "+"
    # to remove the last plus
    command = command[:-1]
    command += ";"
    sing.RunSingularCommand(command)

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
    sing.RunSingularCommand(command)

def poly_eq(name, data):
    if (len(data) != 2):
        raise TypeError
    poly1 = poly_info(data[0])
    poly2 = poly_info(data[1])

    # only support integer ring for coefficients for now
    if poly1.ring.arguments[0] != int_ring_sym:
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

    result = sing.RunSingularCommand("int " + name + " = p1 == p2;")[1]

def polynomial(name, data):
    poly = poly_info(data[0])

    ring_ctor("r", poly.variables)
    poly_ctor(name, poly.terms, poly.ring)

def ideal(name, data):
    poly = poly_info(data)
    ring_ctor("r", poly.variables)
    poly_ctor("p", poly.terms, poly.ring)

    sing.RunSingularCommand("ideal " + name + " = ideal(p)")

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

    sing.RunSingularCommand("ideal " + name + " = groebner(" + arg_str + ");")

def dimension(data):
    poly = poly_info(data)
    ring_ctor("r", poly.variables)
    poly_ctor("p", poly.terms, poly.ring)

    sing.RunSingularCommand("int " + name + " = dim(p)")

# Supported functions
CD_SCSCP2 = ['get_service_description', 'get_allowed_heads', 'is_allowed_head', 'get_signature']
CD_SINGULAR = [
        'polynomial_eq',
        'polynomial',
        'ideal',
        'groebner'
]

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
            self.log.debug('Requested head: %s...' % head)
            
            if call.data.elem.cd == 'scscp2' and head in CD_SCSCP2:
                res = getattr(self, head)(call.data)
            elif call.data.elem.cd == 'singular' and head in CD_SINGULAR:
                #args = [conv.to_python(a) for a in call.data.arguments]
                args = call.data.arguments
                handler = get_handler(head)
                name = makename()
                handler(name, args)
                res = retrieve(name)
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
        return scscp.symbol_set([om.OMSymbol(head, cd='scscp2') for head in CD_SCSCP2]
                                    + [om.OMSymbol(head, cd='singular') for head in CD_SINGULAR],
                                    cdnames=['scscp1'])
    
    def is_allowed_head(self, data):
        head = data.arguments[0]
        return conv.to_openmath((head.cd == 'scscp_trans_1' and head.name in CD_SCSCP_TRANS)
                                    or (head.cd == 'scscp2' and head.name in CD_SCSCP2)
                                    or (head.cd == 'singular'and head.name in CD_SINGULAR)
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
    srv = Server(logger=logger)

    #sing.InitializeSingular("/usr/bin/Singular")
    sing.InitializeSingular("/usr/bin/Singular")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
        srv.server_close()

