def get_span_start(type):
    return '<span class="label ' + type + '">'


def get_span_end():
    return '</span>'


def get_rs_start(type):
    return '<rs type="' + type + '">'


def get_rs_end():
    return '</rs>'


def decorate_text_with_annotations(text, spans, tag="span"):
    """
        Decorate a text using spans, using two style defined by the tag:
            - "span" generated HTML like annotated text
            - "rs" generate XML like annotated text (format SuperMat)
    """
    sorted_spans = list(sorted(spans, key=lambda item: item['offset_start']))
    annotated_text = ""
    start = 0
    for span in sorted_spans:
        type = span['type'].replace("<", "").replace(">", "")
        annotated_text += text[start: span['offset_start']]
        annotated_text += get_span_start(type) if tag == "span" else get_rs_start(type)
        annotated_text += text[span['offset_start']: span['offset_end']]
        annotated_text += get_span_end() if tag == "span" else get_rs_end()

        start = span['offset_end']
    annotated_text += text[start: len(text)]
    return annotated_text
