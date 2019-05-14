FROM debian:stretch

# Put dependencies into /app/
WORKDIR /app/
ADD requirements.txt /app/requirements.txt

# Install dependencies
RUN apt-get update \
    && apt-get install -y \
        git \
        python3-pip \
        libgmp3-dev \
        libsingular4-dev \
        pkg-config \
        singular \
    && python3 -m pip install -r requirements.txt


ADD COPYRIGHT.md /app/COPYRIGHT.md
ADD LICENSE /app/LICENSE
ADD README.md /app/README.md

ADD names.py /app/names.py
ADD test.py /app/test.py
ADD poly_parsing.py /app/poly_parsing.py
ADD singular_server.py /app/singular_server.py

# expose the ports and run the script
EXPOSE 26135
ENV SCSCP_HOST 0.0.0.0
CMD [ "python3", "singular_server.py" ]