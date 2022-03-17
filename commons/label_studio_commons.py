from collections import OrderedDict


def to_label_studio_format_single(text: str, spans: list) -> list:

    sentence_structure = OrderedDict()
    sentence_structure['data'] = {
        "text": text
    }
    sentence_structure['predictions'] = [
        {
            'model_version': '1',
            'result': [
                {'id': id_,
                 'from_name': 'label',
                 'to_name': 'text',
                 'type': 'labels',
                 'value': {'start': spans['offset_start'], 'end': spans['offset_end'],
                           'text': spans['text'],
                           'labels': [spans['type'].replace('<', '').replace('>', '')]}
                 } for id_, spans in enumerate(spans)
            ]
        }
    ]

    return sentence_structure
