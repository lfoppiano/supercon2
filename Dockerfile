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
COPY supercon2/ /opt/service/supercon2
COPY commons/ /opt/service/commons
COPY process/ /opt/service/process
COPY resources/version.txt /opt/service/resources/

# extract version
COPY .git ./.git
RUN git rev-parse --short HEAD > /opt/service/resources/version.txt
RUN rm -rf ./.git

ENV VIRTUAL_ENV=/opt/service/venv
RUN python3.9 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip --version

RUN python3 -m pip install pip --upgrade
RUN pip install -r ./requirements.txt

EXPOSE 8080

CMD ["python3", "-m", "supercon2", "--config", "supercon2/config.yaml"]