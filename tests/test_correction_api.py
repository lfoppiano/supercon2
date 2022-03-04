from bson import ObjectId

from supercon2.service import update_record, _update_record


def test_update_record(mongodb):
    assert 'tabular' in mongodb.list_collection_names()

    records_by_document_before = mongodb.tabular.find({'hash': '48ba234393'}).count()

    new_record = {"rawMaterial": "thin films Mg B2",
                  "materialId": "-964232725",
                  "formula": "Mg B2",
                  "shape": "thin films",
                  "criticalTemperature": "23 K",
                  "criticalTemperatureId": "-1165456602",
                  "section": "body",
                  "subsection": "figure",
                  "sentence": "It has the value of 27 K and is higher than T c of single crystals (23 K and 22 K) 22,23 and thin films (24.5 K). 24 Recent results show that",
                  "hash": "48ba234393",
                  "timestamp": {"$date": "2022-01-14T06:42:24.569Z"},
                  "title": "A defect detection method for MgB 2 superconducting and iron-based Ba(Fe,Co) 2 As 2 wires",
                  "doi": "10.1063/1.4947056]",
                  "authors": "D Gajda, ) A Morawski, A Zaleski, A Yamamoto, T Cetner",
                  "year": 2016}

    original_identifier = '61e136f56e3ec3a715592988'
    original_identifier_object_id = ObjectId(original_identifier)
    inserted_id = _update_record(original_identifier_object_id, new_record, mongodb)

    records_by_document_after = mongodb.tabular.find({'hash': '48ba234393'}).count()

    assert records_by_document_after > records_by_document_before

    final_record = mongodb.tabular.find_one(inserted_id)
    assert final_record['status'] == "valid"
    assert final_record['type'] == "manual"
    assert final_record['previous'] == original_identifier_object_id
    assert str(final_record['_id']) != original_identifier

    old_record_from_db = mongodb.tabular.find_one({'_id': original_identifier_object_id})

    assert old_record_from_db['status'] == "obsolete"
    assert old_record_from_db['type'] == "automatic"

    assert old_record_from_db['timestamp'] != final_record['timestamp']
