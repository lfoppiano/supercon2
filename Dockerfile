FROM python:3.10-slim

ENV LANG C.UTF-8

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
    git \
    build-essential gcc\
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
RUN git rev-parse --short HEAD > /opt/service/resources/revision.txt
RUN rm -rf ./.git

ENV VIRTUAL_ENV=/opt/service/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip --version

RUN python3 -m pip install pip --upgrade --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org
RUN pip install -r ./requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org

EXPOSE 8080

CMD ["python3", "-m", "supercon2", "--config", "supercon2/config.yaml","--debug", "development"]