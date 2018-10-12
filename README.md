# MitM_Singular for Singular

This package provides functionality to run Singular in a Math-in-the-Middle Virtual
Research Environment for Discrete Mathematics (otherwise known as OpenDreamKit
https://www.opendreamkit.org)

## Installation

Several things need to be installed in order to run `singular_server.py`.  In
Ubuntu, the following commands should do the trick:

    sudo apt install python3-pip libsingular4-dev pkg-config
    pip3 install --user openmath scscp pysingular termcolor

Then run the server with:

    git clone https://github.com/markuspf/MitM_Singular.git
    cd MitM_Singular
    python3 singular_server.py

## Example

To run the server, enter the MitM_Singular directory and call
`python3 singular_server.py`

To interact with the server from Python, and compute the Groebner base of a set
of polynomials, open an interactive Python window by calling `python3` on the
command line, and then enter:

    import openmath.openmath as om, scscp, poly_parsing as parse, lxml.etree as etree
    client = scscp.SCSCPCLI("localhost", 26135)
    list_of_strings = ["3*x1+2*x2", "3*x2+2*x3", "3*x1+2*x4", "3*x3+2*x4", "2*x3+3*x4", "2*x1+3*x2", "2*x1+3*x4", "2*x2+3*x3"]
    list_of_polys = [parse.parse_polynomial(str) for str in list_of_strings]
    l = om.OMApplication(om.OMSymbol("list", "list1"), list_of_polys)
    g = client.heads.singular.groebner([l])

Then to see the output in OpenMath XML, enter:

    import lxml.etree as etree, openmath.encoder as enc
    etree.tostring(enc.encode_xml(g))

## Bug reports and feature requests

Please submit bug reports and feature requests via our GitHub issue tracker:

  <https://github.com/markuspf/MitM_Singular/issues>


# License

MitM_Singular is free software; you can redistribute it and/or modify it under
the terms of the BSD 3-clause license.

For details see the files COPYRIGHT.md and LICENSE.

# Acknowledgement

<table class="none">
<tr>
<td>
  <img src="http://opendreamkit.org/public/logos/Flag_of_Europe.svg" width="128">
</td>
<td>
  This infrastructure is part of a project that has received funding from the
  European Union's Horizon 2020 research and innovation programme under grant
  agreement No 676541.
</td>
</tr>
</table>
