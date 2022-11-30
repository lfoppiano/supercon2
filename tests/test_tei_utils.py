from commons.tei_utils import transform_in_tei


def test_database():
    sentences = [
        {
        "text": "We are studying the material La 3 A 2 Ge 2 (A = Ir, Rh).",
        "type": "sentence",
        "spans": [
            {
                "id": "-256798580",
                "text": "La 3 A 2 Ge 2 (A = Ir, Rh)",
                "formattedText": "La 3 A 2 Ge 2 (A = Ir, Rh)",
                "type": "<material>",
                "linkable": True,
                "source": "superconductors",
                "offset_start": 29,
                "offset_end": 55,
                "token_start": 10,
                "token_end": 32
            }
        ]
    },
        {
            "text": "The critical temperature T C = 4.7 K discovered for La 3 Ir 2 Ge 2 in this work is by about 1.2 K higher than that found for La 3 Rh 2 Ge 2.",
            "type": "sentence",
            "spans": [
                {
                    "id": "-549992374",
                    "text": "critical temperature",
                    "type": "<tc>",
                    "linkable": False,
                    "source": "superconductors",
                    "offset_start": 4,
                    "offset_end": 24,
                    "token_start": 2,
                    "token_end": 6
                },
                {
                    "id": "173078943",
                    "text": "T C",
                    "type": "<tc>",
                    "linkable": False,
                    "source": "superconductors",
                    "offset_start": 25,
                    "offset_end": 28,
                    "token_start": 6,
                    "token_end": 10
                },
                {
                    "id": "-1399809843",
                    "text": "4.7 K",
                    "type": "<tcValue>",
                    "linkable": True,
                    "source": "superconductors",
                    "links": [
                        {
                            "targetId": "1276417214",
                            "targetText": "La 3 Ir 2 Ge 2",
                            "targetType": "<material>",
                            "type": "vicinity"
                        }
                    ],
                    "offset_start": 31,
                    "offset_end": 36,
                    "token_start": 12,
                    "token_end": 18
                },
                {
                    "id": "1276417214",
                    "text": "La 3 Ir 2 Ge 2",
                    "formattedText": "La 3 Ir 2 Ge 2 ",
                    "type": "<material>",
                    "linkable": True,
                    "source": "superconductors",
                    "links": [
                        {
                            "targetId": "-1399809843",
                            "targetText": "4.7 K",
                            "targetType": "<tcValue>",
                            "type": "vicinity"
                        }
                    ],
                    "attributes": {
                        "material0_formula_rawValue": "La 3 Ir 2 Ge 2",
                        "material0_formula_formulaComposition_La": "3",
                        "material0_formula_formulaComposition_Ir": "2",
                        "material0_formula_formulaComposition_Ge": "2",
                        "material0_rawTaggedValue": "<formula>La 3 Ir 2 Ge 2</formula> ",
                        "material0_resolvedFormulas_0_rawValue": "La 3 Ir 2 Ge 2",
                        "material0_resolvedFormulas_0_formulaComposition_La": "3",
                        "material0_resolvedFormulas_0_formulaComposition_Ir": "2",
                        "material0_resolvedFormulas_0_formulaComposition_Ge": "2",
                        "material0_class": "Alloys"
                    },
                    "offset_start": 52,
                    "offset_end": 66,
                    "token_start": 22,
                    "token_end": 34
                },
                {
                    "id": "1932045977",
                    "text": "1.2 K",
                    "type": "<tcValue>",
                    "linkable": False,
                    "source": "quantities",
                    "offset_start": 92,
                    "offset_end": 97,
                    "token_start": 46,
                    "token_end": 52
                },
                {
                    "id": "-764465102",
                    "text": "La 3 Rh 2 Ge 2",
                    "formattedText": "La 3 Rh 2 Ge 2",
                    "type": "<material>",
                    "linkable": True,
                    "source": "superconductors",
                    "attributes": {
                        "material0_formula_rawValue": "La 3 Rh 2 Ge 2",
                        "material0_formula_formulaComposition_La": "3",
                        "material0_formula_formulaComposition_Rh": "2",
                        "material0_formula_formulaComposition_Ge": "2",
                        "material0_rawTaggedValue": "<formula>La 3 Rh 2 Ge 2</formula>",
                        "material0_resolvedFormulas_0_rawValue": "La 3 Rh 2 Ge 2",
                        "material0_resolvedFormulas_0_formulaComposition_La": "3",
                        "material0_resolvedFormulas_0_formulaComposition_Rh": "2",
                        "material0_resolvedFormulas_0_formulaComposition_Ge": "2",
                        "material0_class": "Alloys"
                    },
                    "offset_start": 125,
                    "offset_end": 139,
                    "token_start": 62,
                    "token_end": 73
                }
            ]
        }
    ]

    biblio = {
        "title": "This is the title",
        "doi": "DOI!"
    }

    print(transform_in_tei(sentences, biblio))
