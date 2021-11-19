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

> conda create -n supercon2 pip python=3.9 

> conda activate supercon2

check that pip is the correct one in the conda environment: 

> which pip 

(pip should come from `.envs/supercuration/bin/pip` or something like that. In negative case, and eventually unset it 

> unset pip 

> python -m supercon2 --config supercon2/config.json 

## Scripts

1. `supercon_batch_mongo_extraction` (save PDF, extract JSON response)
2. `supercon_bath_mongo_compute_table` (compute tables and save back)


