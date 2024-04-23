### BASE ###

FROM ubuntu:22.04 as base
WORKDIR /app
RUN apt update

# misc
RUN apt install screen -y

# postgres
RUN DEBIAN_FRONTEND=noninteractive apt install -y postgresql

# python
RUN apt install software-properties-common -y
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install -y python3.12 python3.12-distutils python3.12-dev python3.12-venv
RUN python3.12 -m ensurepip --upgrade

# node
RUN apt install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_21.x | bash - && apt-get install -y nodejs

# python venv
#   create it here before copying source code so that
#   we don't need to reinstall deps after every change
RUN python3.12 -m venv venv
COPY ./core/requirements.txt .
RUN ./venv/bin/python -m pip install -r requirements.txt
RUN rm requirements.txt

### DEV ###

FROM base AS dev
COPY . .

RUN mv /app/venv /app/core/venv