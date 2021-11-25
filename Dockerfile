FROM python:rc-slim

ENV LANG C.UTF-8

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
    git \
    python3.9 python3.9-venv python3.9-dev python3.9-distutil build-essential gcc\
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN mkdir -p /opt/service/venv

WORKDIR /opt/service

COPY requirements.txt .
COPY supercon2 /opt/service
COPY process /opt/service

ENV VIRTUAL_ENV=/opt/linking/venv
RUN python3.9 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip --version

RUN python3 -m pip install pip --upgrade
RUN pip install -r ./requirements.txt

EXPOSE 8080

CMD ["python3", "-m", "supercond2", "--config", "supercon2/config.yaml"]