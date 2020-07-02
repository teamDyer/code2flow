FROM ubuntu:18.04
LABEL maintainer="Calvin Rose"
ENV DEBIAN_FRONTEND=noninteractive

# Install
RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get -y install python3 python3-pip \
    && pip3 install pipenv

# Build frontend -> /app/frontend
COPY . /satellite/
WORKDIR /satellite/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
# Reproducible builds
ENV PYTHONHASHSEED=12345
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --python `which python3`

# Build satellite binary
CMD pipenv run pyinstaller --bootloader-ignore-signals -F satellite.py