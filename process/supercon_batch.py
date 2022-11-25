# Script to extract superconductor and materials name from PDFs
import argparse
import csv
import json
import os
import sys
from pathlib import Path

from process.grobid_client_generic import GrobidClientGeneric

header_row = ["Raw material", "Raw material ID",
              "Name", "Formula", "Doping", "Shape", "Class", "Fabrication", "Substrate", "variables",
              # "Unit-cell-type", "Unit-cell-type ID",
              # "Space group", "Space group ID",
              # "Crystal structure", "Crystal structure ID",
              "Critical temperature", "Critical temperature ID",
              "Measurement method", #"Measurement method ID",
              "Applied pressure", #"Applied pressure ID",
              "Link type",
              "Section", "Subsection", "Sentence",
              "Path", "Filename"]


def decode(response_string):
    try:
        return json.loads(response_string)
    except ValueError as e:
        return "Value error: " + str(e)
    except TypeError as te:
        return "Type error: " + str(te)


def process_file(grobid_client, source_path, format: str, task="processPDF"):
    print("Processing file " + str(source_path))
    accept_header_value = "application/json" if format == 'json' else "text/csv"

    r, error_code = grobid_client.process_pdf(str(source_path), task, headers={"Accept": accept_header_value})
    if r is None:
        print("Response is empty or without content for " + str(source_path) + ". Moving on. ")
        return []
        # raise Exception("Response is None for " + str(source_path) + ". Moving on. ")
    else:
        if format == 'json':
            output = json.loads(r)
        else:
            reader = csv.reader(r.split("\n"))
            next(reader, None)
            output = [row for row in reader if len(row) > 0]

    return output


def write_data(output_path, data, format, aggregated_output=None):
    with open(output_path, 'w') as f:
        if format == 'json':
            json.dump(data, f)
        else:
            delimiter = ',' if format == 'csv' else '\t'
            writer = csv.writer(f, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerow(header_row)
            for row in data:
                writer.writerow(row)

    if aggregated_output is not None and format != 'json':
        with open(aggregated_output, 'a') as af:
            delimiter = ',' if format == 'csv' else '\t'
            writer = csv.writer(af, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_ALL)
            for row in data:
                writer.writerow(row)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Extract superconductor materials and properties in CSV/TSV/JSON")

    parser.add_argument("--input", help="Input file or directory", type=Path, required=True)
    parser.add_argument("--output", help="Output directory", type=Path, required=True)
    parser.add_argument("--config", help="Config file", type=Path, required=False, default='./config.yaml')
    parser.add_argument("--recursive", action="store_true", default=False,
                        help="Process input directory recursively. If input is a file, this parameter is ignored.")
    parser.add_argument("--format", default='csv', choices=['tsv', 'csv', 'json'],
                        help="Output format.")
    parser.add_argument("--task", default='processPDF', choices=['processPDF', 'processPDF_disableLinking'],
                        help="Tasks to be executed.")

    args = parser.parse_args()

    input_path = args.input
    output_path = args.output
    recursive = args.recursive
    output_format = args.format
    config = args.config
    task = args.task

    grobid_client = GrobidClientGeneric(config_path=config)

    if os.path.isdir(input_path):
        if not os.path.isdir(output_path):
            print("--output should specify always a directory")
            sys.exit(-1)
        path_list = []

        if recursive:
            for root, dirs, files in os.walk(input_path):
                for file_ in files:
                    if not file_.lower().endswith(".pdf"):
                        continue

                    abs_path = os.path.join(root, file_)
                    output_filename = Path(abs_path).stem
                    parent_dir = Path(abs_path).parent
                    if os.path.isdir(output_path):
                        output_ = Path(str(parent_dir).replace(str(input_path), str(output_path)))
                        output_filename_with_extension = str(output_filename) + '.' + output_format
                        output_path_with_filename_and_extension = os.path.join(output_, output_filename_with_extension)
                        # else:
                        #     output_path = os.path.join(parent_dir, output_filename + ".tei.xml")

                        path_list.append((Path(abs_path), output_path_with_filename_and_extension))

        else:
            path_list = Path(input_path).glob('*.pdf')

        aggregated_output_file = os.path.join(output_path, "aggregated_output" + "." + output_format)
        with open(aggregated_output_file, 'w') as af:
            delimiter = ',' if output_format == 'csv' else '\t'
            writer = csv.writer(af, delimiter=delimiter, quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerow(header_row)


        # output_data = []
        for input_file_path, output_file_path in path_list:
            extracted_data = process_file(grobid_client, input_file_path, output_format, task=task)
            if len(extracted_data) > 0:
                input_path = Path(input_file_path)
                for extracted_row in extracted_data:
                    extracted_row.extend([input_path.name, str(input_path)])

                abs_parent_path = Path(output_file_path).parent
                if not os.path.exists(abs_parent_path):
                    os.makedirs(abs_parent_path)
                write_data(output_file_path, extracted_data, output_format,
                           aggregated_output=aggregated_output_file)

    elif os.path.isfile(input_path):
        extracted_data = process_file(grobid_client, input_path, output_format, task=task)
        output_filename = os.path.join(output_path, input_path.stem + "." + output_format)

        # write_rows(output_filename, header_row)
        write_data(output_filename, extracted_data, output_format)
