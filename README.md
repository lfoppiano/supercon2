# Supercon 2

**Work in progress**

Superconductors material database rebuild with semi-automatic extraction system interface
This interface allows extraction and visualisation of material and properties from superconductors-related papers.
It can be used to visualise the harvested information from processing PDFs using [Grobid Superconductor](https://github.com/lfoppiano/grobid-superconductors)

## Interface

Main features
 - Visualisation
 - Filtering
 - export in Excel, JSON, XML, etc...

### Process

Main features:
 - versioning
 - skip/force reprocessing
 - simple logging (successes and failures divided by process steps)

## Getting started

### Docker

### Development

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


## Scripts

1. Process a PDF document and extracts the JSON response
```
python -m process.supercon_batch_mongo_extraction --config ./process/config.yaml --input <your_pdf_input_directory>
```

2. Transforms the JSON document in tabular format 

```
python -m process.supercon_batch_mongo_compute_table --config ./process/config.yaml
```
