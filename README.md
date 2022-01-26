# Supercon 2

**Work in progress**
This project provides the service and processes to build the next version of [Supercon](http://supecon.nims.go.jp). 
The service provides the API and interface which allows the visualisation of material and properties extracted from superconductors-related papers.
The process is composed by scripts that interact with [Grobid Superconductor](https://github.com/lfoppiano/grobid-superconductors) to extract materials information from large quantities of PDFs.

## Service API and visualisation interface

The service API provides the following features: 
 - Visualisation of records of extracted materials-properties and enhanced PDFS with annotations
 - Filter records through columns search
 - export in Excel, JSON, XML, etc...

![record-list.png](docs/images/record-list.png)

![pdf-view.png](docs/images/pdf-view.png)

### Getting started

#### Docker
TBD 

#### Local development

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

To run the service you can use: 

```
python -m supercon2 --config supercon2/config.json
```


### Processes

The processes are composed by a set of python scripts that were built under the following principles: 
 - versioning
 - skip/force reprocessing
 - simple logging (successes and failures divided by process steps)

#### Functionalities

##### PDF processing and extraction 

Extract superconductor materials and properties and save them on MongoDB - extraction

```
usage: supercon_batch_mongo_extraction.py [-h] --input INPUT --config CONFIG [--num-threads NUM_THREADS] [--only-new] [--database DATABASE] [--verbose]

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT         Input directory
  --config CONFIG       Configuration file
  --num-threads NUM_THREADS, -n NUM_THREADS
                        Number of concurrent processes
  --only-new            Processes only documents that have not record in the database
  --database DATABASE, -db DATABASE
                        Force the database name which is normally read from the configuration file
  --verbose             Print all log information
```

Example: 
```
python -m process.supercon_batch_mongo_extraction --config ./process/config.yaml --input <your_pdf_input_directory>
```


##### Conversion from document representation to material-properties records

Process extracted documents and compute the tabular format: 

```
usage: supercon_batch_mongo_compute_table.py [-h] --config CONFIG [--num-threads NUM_THREADS] [--database DATABASE] [--force] [--verbose]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       Configuration file
  --num-threads NUM_THREADS, -n NUM_THREADS
                        Number of concurrent processes
  --database DATABASE, -db DATABASE
                        Set the database name which is normally read from the configuration file
  --force, -f           Re-process all the records and replace existing one.
  --verbose             Print all log information

```
Example: 
```
python -m process.supercon_batch_mongo_compute_table --config ./process/config.yaml
```

##### Feedback manual corrections from Excel to the database 

Feedback to supercon2 corrections from an Excel file


```
usage: feedback_corrections.py [-h] --corrections CORRECTIONS --config CONFIG [--dry-run] [--database DATABASE] [--verbose]

optional arguments:
  -h, --help            show this help message and exit
  --corrections CORRECTIONS
                        Correction file (csv or excel)
  --config CONFIG       Configuration file
  --dry-run             Perform the operations without writing on the database.
  --database DATABASE, -db DATABASE
                        Force the database name which is normally read from the configuration file
  --verbose             Print all log information

```
Example: 
```
python -m process.supercon_batch_mongo_compute_table --config ./process/config.yaml
```
