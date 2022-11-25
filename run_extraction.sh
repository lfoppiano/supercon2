#!/bin/bash

INPUT=$1

if [ ! -d "${INPUT}" ]
then echo "Missing parameter input directory. Usage ./run_extraction.sh /input/directory"; exit -1;
fi

python -u -m process.supercon_batch_mongo_extraction --config process/config.yaml  --num-threads 6 --input $1 --only-new

# python -m process.supercon_batch_mongo_extraction  --input /data/workspace/archives/arxiv/pre_2007/supr-cond  --config process/config.yaml --num-threads 6 --only-new --verbose > extraction_pre2007.log &