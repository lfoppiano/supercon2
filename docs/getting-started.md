# Getting started

## Docker

Docker can be built with:

> docker build -t lfoppiano/supercon2:1.2 --file Dockerfile .

and run:

> docker run -rm -p 8080 -v ./supercon2/config-docker.yaml:/opt/service/supercon2/config.yaml:ro lfoppiano/supercon2:1.2

For connecting to mongodb is possible to connect directly to the mongodb IP (to be specified in `config-docker.yaml`),
if this is not possible then it's recommended to use docker-compose.

## Docker compose

The docker compose is going to mount the volume `resources/mongo` as `/data/db` in the container. And mapping the
mongodb container with port 27018 (to avoid conflicts with the default mongodb port).

The configuration file `supercon2/config-docker.yaml` is also mapped in the supercon2
container `/opt/service/supercon2/config.yaml`

Docker compose is executed by running:

> docker-compose up

and shut down:

> docker-compose down

### Local development

We recommend to use CONDA
```
conda create -n supercon2 pip python=3.9
conda activate supercon2
```

check that pip is the correct one in the conda environment:

```
which pip
```

pip should be something like `....supercon2/bin/pip`. If not you should unset it with:

```
unset pip
```

Download the source:

```
git clone https://github.com/lfoppiano/supercon2 supercon2

cd supercon2 
```

Install dependencies:

```
pip install -r requirements.txt
```

Install mongodb (the exact command will depends on the OS)

Load sample data on the database supercon2
```
unzip resources/data/supercon_sample.zip -d resources/data

mongorestore localhost:27017/supercon_sample resources/data/supercon_sample
```
**NOTE**: make sure the `db` entry is correctly set to `supercon_sample` in `supercon2/config.yaml`,

Finally, to run the service you can use:

```
python -m supercon2 --config supercon2/config.yaml
```
