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
