import argparse
import hashlib
import os
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from bson import ObjectId
from pymongo import UpdateOne

from commons.annotations_utils import decorate_text_with_annotations
from process.grobid_client_generic import GrobidClientGeneric
from process.supercon_batch_mongo_extraction import connect_mongo


# multiprocessing.set_start_method("fork")

def group_by(input, field: str):
    dict = {}
    for elem in input:
        if elem[field] not in dict:
            dict[elem[field]] = []
        elem_clean = elem.copy()
        del elem_clean[field]
        dict[elem[field]].append(elem_clean)
    return dict


def generate_features(token, previous_token):
    token_text = token['text']
    vector = [token_text, str.lower(token_text)] + [token_text[0:n] for n in range(1, 5)] + [token_text[n:] for n in
                                                                                             range(-5, -1)]
    capital = "NOCAPS"
    if token_text.isupper():
        capital = "ALLCAPS"
    elif capital[0].isupper():
        capital = "INITCAPS"

    vector.append(capital)

    is_digit = "NODIGIT"
    if token_text.isdigit():
        is_digit = "ALLDIGIT"
    elif bool(re.compile('\d').search(token_text)):
        is_digit = "CONTAINSDIGIT"

    vector.append(is_digit)

    single_char = 1 if len(text) == 1 else 0
    vector.append(single_char)

    punct = "NOPUNCT"
    if bool(re.compile('^[\,\:;\?\.]+$').search(token_text)):
        punct = "PUNCT"
    if any(string == token_text for string in ["(", "["]):
        punct = "OPENBRACKET"
    elif any(string == token_text for string in [")", "]"]):
        punct = "ENDBRACKET"
    elif any(string == token_text for string in [".", "⋅", "•", "·"]):
        punct = "DOT"
    elif token_text == ",":
        punct = "COMMA"
    elif any(string == token_text for string in ["-", "−", "–"]):
        punct = "HYPHEN"
    elif any(string == token_text for string in ["\"", "'", "`"]):
        punct = "QUOTE"

    vector.append(punct)

    # shadow number
    vector.append(shadowNumbers(token_text))

    # word shape
    vector.append(wordShape(token_text))

    # word shape trimmed
    vector.append(wordShapeTrimmed(token_text))

    # Font status
    if previous_token is None:
        font_status = "NEWFONT"
    elif token['font'] != previous_token['font']:
        font_status = "NEWFONT"
    else:
        font_status = "SAMEFONT"

    vector.append(font_status)

    # Font size
    vector.append(token['fontSize'])

    vector.append(token['bold'])

    vector.append(token['italic'])

    vector.append(token['style'])

    vector.append(False)

    return vector


def shadowNumbers(string):
    i = 0
    if string is None:
        return string
    res = ""
    while i < len(string):
        c = string[i]
        if c.isdigit():
            res += 'X'
        else:
            res += c
        i += 1
    return res


def wordShape(word):
    shape = ""
    for c in word:
        if c.isalpha():
            if c.isupper():
                shape += "X"
            else:
                shape += "x"
        elif c.isdigit():
            shape += "d"
        else:
            shape += c

    finalShape = shape[0]

    suffix = ""
    if len(word) > 2:
        suffix = shape[-2:]
    elif len(word) > 1:
        suffix = shape[-1:]

    middle = ""
    if len(shape) > 3:
        ch = shape[1]
        for i in range(1, len(shape) - 2):
            middle += ch
            while ch == shape[i] and i < len(shape) - 2:
                i += 1
            ch = shape[i]

        if ch != middle[-1]:
            middle += ch

    return finalShape + middle + suffix


def wordShapeTrimmed(word):
    shape = ""
    for c in word:
        if c.isalpha():
            if c.isupper():
                shape += "X"
            else:
                shape += "x"
        elif c.isdigit():
            shape += "d"
        else:
            shape += c

    middle = ""

    ch = shape[0]
    for i in range(len(shape)):
        middle += ch
        while ch == shape[i] and i < len(shape) - 1:
            i += 1
        ch = shape[i]

    if ch != middle[-1]:
        middle += ch

    return middle


xmlTemplate = """<tei xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
        <fileDesc xml:id="_0">
            <titleStmt/>
            <publicationStmt>
                <publisher>National Institute for Materials Science (NIMS), Tsukuba, Japan</publisher>
                <availability>
                    <licence target="http://nims.go.jp">
                        <p>Copyright National Institute for Materials Science (NIMS), Tsukuba, Japan</p>
                    </licence>
                </availability>
            </publicationStmt>
        </fileDesc>
        <encodingDesc>
            <appInfo>
                <application version="project.version" ident="grobid-superconductors">
                    <ref target="https://github.com/lfoppiano/grobid-superconductors">A machine learning software for extracting materials and their properties from scientific literature.</ref>
                </application>
            </appInfo>
        </encodingDesc>
        <profileDesc>
            <abstract/>            
        </profileDesc>
    </teiHeader>
    <text xml:lang="en">
        <body/>
    </text>
</tei>"""


def get_text_under_body(soup):
    children = soup.findChildren('text')
    return children[0] if children is not None and len(
        children) > 0 else None


def write_output(output_data):
    for hash in output_data.keys():
        output_xml_path = os.path.join(output, hash + ".tei.xml")
        output_features_path = os.path.join(output, hash + ".features.txt")

        with open(output_xml_path, 'w') as fo:
            soup = BeautifulSoup(xmlTemplate, 'xml')
            header = soup.find("teiHeader")
            header_pretty = header.prettify()

            with open(output_features_path, 'w') as fo_features:
                processed = []
                for example in output_data[hash]:
                    text_hash = example['id']
                    if text_hash in processed:
                        continue
                    else:
                        processed.append(text_hash)

                    tag = BeautifulSoup(
                        '<p>\n<s error_type="' + example["error_type"] + '">' + example['xml'] + '</s>\n</p>', 'xml')
                    text_tag = get_text_under_body(soup)
                    text_tag.body.append(tag)

                    for token_features in example['features']:
                        fo_features.write(" ".join([str(t) for t in token_features]) + "\n")

                    fo_features.write("\n\n")

                fo_features.flush()

            cooked_soup = str(soup)
            cooked_soup = cooked_soup.replace(str(header), header_pretty)
            fo.write(str(cooked_soup))
            fo.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Fetch training data from Supercon 2.")
    parser.add_argument("--config", help="Configuration file", type=Path, required=True)
    parser.add_argument("--database", "-db",
                        help="Set the database name which is normally read from the configuration file", type=str,
                        required=False)
    # parser.add_argument("--force", help="Force to export all training data available, even if they have been already exported. ",
    #                     action="store_true", default=False)
    parser.add_argument("--verbose",
                        help="Print all log information", action="store_true", required=False, default=False)
    parser.add_argument("--output", help="Output directory", required=True)

    args = parser.parse_args()
    config_path = args.config
    db_name = args.database
    # force = args.force
    verbose = args.verbose
    output = args.output

    if not os.path.isdir(output):
        print("The output path must be a directory:", output)
        parser.print_help()
        sys.exit(-1)

    if not os.path.exists(config_path):
        print("The config file does not exists. ")
        parser.print_help()
        sys.exit(-1)

    config = GrobidClientGeneric().load_yaml_config_from_file(config_path)

    if db_name is None:
        db_name = config["mongo"]["db"]
    else:
        db_name = db_name

    connection = connect_mongo(config=config)
    db = connection[db_name]
    training_data_collection = db.get_collection("training_data")

    training_data_list = list(training_data_collection.find({'status': 'new'}))

    training_data_by_document = group_by(training_data_list, 'hash')
    tabular_collection = db.get_collection("tabular")

    output_data = {}
    updates = []
    for hash in training_data_by_document.keys():
        output_data[hash] = []
        for td in training_data_by_document[hash]:
            m = hashlib.sha256()
            text_ = td['text'] + str(len(td['spans']))
            text_hash = m.update(text_.encode("utf-8"))
            id = m.hexdigest()
            corrected_id = td['corrected_record_id']
            document = tabular_collection.find_one({"_id": ObjectId(corrected_id)}, {"error_type": 1})

            if document is None:
                error_type = "N/A (doc missing)"
            elif 'error_type' in document:
                error_type = document['error_type']
            elif 'status' in document:
                error_type = document['status']
            else:
                error_type = "N/A"

            text = td['text']

            if verbose:
                print(hash, "-", text)

            tokens = []
            if 'tokens' in td:
                tokens = td['tokens']

            spans = []
            if 'spans' in td:
                spans = td['spans']

            annotated_text = decorate_text_with_annotations(text, spans, "rs")

            features = []
            previous_token = None
            for token in tokens:
                if token['text'] == " ":
                    continue
                features_vector = generate_features(token, previous_token)

                features.append(features_vector)
                # print(token)
                previous_token = token

            output_data[hash].append(
                {"id": text_hash, "xml": annotated_text, "features": features, "error_type": error_type})

            updates.append(UpdateOne({'_id': td['_id']}, {'$set': {'status': 'exported'}}))

    write_output(output_data)
    if len(updates) > 0:
        op_result = training_data_collection.bulk_write(updates)

        print("Exported records:", op_result.modified_count)
    else:
        print("No records to export.")
