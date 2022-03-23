from unittest.mock import MagicMock

from bson import ObjectId

from supercon2.service import _update_record


def test_update_record_should_update_record(mongodb):
    assert 'tabular' in mongodb.list_collection_names()

    records_by_document_before = len(list(mongodb.tabular.find({'hash': '48ba234393'})))

    new_record = {"rawMaterial": "thin films Mg B2",
                  "materialId": "-964232725",
                  "formula": "Mg B2",
                  "shape": "thin films",
                  "criticalTemperature": "23 K",
                  "criticalTemperatureId": "-1165456602",
                  "appliedPressure": "3 GPa",
                  "section": "body",
                  "subsection": "figure",
                  "sentence": "It has the value of 27 K and is higher than T c of single crystals (23 K and 22 K) 22,23 and thin films (24.5 K). 24 Recent results show that",
                  "hash": "48ba234393",
                  "title": "A defect detection method for MgB 2 superconducting and iron-based Ba(Fe,Co) 2 As 2 wires",
                  "doi": "10.1063/1.4947056",
                  "authors": "D Gajda, ) A Morawski, A Zaleski, A Yamamoto, T Cetner",
                  "year": 2016}

    original_identifier = '61e136f56e3ec3a715592988'
    original_identifier_object_id = ObjectId(original_identifier)
    inserted_id = _update_record(original_identifier_object_id, new_record, mongodb)

    records_by_document_after = len(list(mongodb.tabular.find({'hash': '48ba234393'})))

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

    assert final_record['appliedPressure'] == "3 GPa"


def test_update_record_should_create_training_data(mongodb):
    assert 'tabular' in mongodb.list_collection_names()

    training_data_by_document_before = len(list(mongodb.training_data.find({'hash': '48ba234393'})))

    new_record = {"rawMaterial": "thin films Mg B2",
                  "materialId": "-964232725",
                  "formula": "Mg B2",
                  "shape": "thin films",
                  "criticalTemperature": "23 K",
                  "criticalTemperatureId": "-1165456602",
                  "appliedPressure": "3 GPa",
                  "section": "body",
                  "subsection": "figure",
                  "sentence": "It has the value of 27 K and is higher than T c of single crystals (23 K and 22 K) 22,23 and thin films (24.5 K). 24 Recent results show that",
                  "hash": "48ba234393",
                  "title": "A defect detection method for MgB 2 superconducting and iron-based Ba(Fe,Co) 2 As 2 wires",
                  "doi": "10.1063/1.4947056",
                  "authors": "D Gajda, ) A Morawski, A Zaleski, A Yamamoto, T Cetner",
                  "year": 2016}

    original_identifier = '61e136f56e3ec3a715592988'
    original_identifier_object_id = ObjectId(original_identifier)
    inserted_id = _update_record(original_identifier_object_id, new_record, mongodb)

    training_data_by_document_after = len(list(mongodb.training_data.find({'hash': '48ba234393'})))
    assert training_data_by_document_after > training_data_by_document_before

    new_training_data = mongodb.training_data.find_one({"corrected_record_id": str(inserted_id)})

    assert new_training_data is not None
    assert new_training_data['status'] == 'new'


def test_update_record_with_failure_should_rollback(mongodb, mocker: MagicMock):
    def write_training_data_mock(a, b, c, d):
        raise Exception("Mocking bird")

    mocker.patch('supercon2.service.write_raw_training_data', write_training_data_mock)

    assert 'tabular' in mongodb.list_collection_names()

    records_by_document_before = len(list(mongodb.tabular.find({'hash': '48ba234393'})))
    training_data_before = len(list(mongodb.training_data.find({'hash': '48ba234393'})))

    new_record = {}

    original_identifier = '61e136f56e3ec3a715592988'
    original_identifier_object_id = ObjectId(original_identifier)
    inserted_id = _update_record(original_identifier_object_id, new_record, mongodb)

    assert inserted_id is None

    records_by_document_after = len(list(mongodb.tabular.find({'hash': '48ba234393'})))
    training_data_after = len(list(mongodb.training_data.find({'hash': '48ba234393'})))

    assert records_by_document_after == records_by_document_before

    old_record_from_db = mongodb.tabular.find_one({'_id': original_identifier_object_id})

    assert old_record_from_db['status'] == "valid"
    assert old_record_from_db['type'] == "automatic"

    assert training_data_after == training_data_before
