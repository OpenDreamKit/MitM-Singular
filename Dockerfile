FROM debian:stretch

# Install dependencies
RUN apt-get update \
    && apt-get install -y \
        python3-pip \
        libgmp3-dev \
        libsingular4-dev \
        pkg-config \
        singular \
    && pip3 install openmath scscp pysingular termcolor

# Put this repository into /app/
RUN mkdir /app/
WORKDIR /app/

ADD COPYRIGHT.md /app/COPYRIGHT.md
ADD LICENSE /app/LICENSE
ADD README.md /app/README.md

ADD poly_parsing.py /app/poly_parsing.py
ADD singular_server.py /app/singular_server.py

# expose the ports and run the script
EXPOSE 26135
ENV SCSCP_HOST 0.0.0.0
CMD [ "python3", "singular_server.py" ]