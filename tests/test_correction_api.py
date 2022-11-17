from unittest.mock import MagicMock

import pytest
from bson import ObjectId

from commons.correction_utils import post_process_fields
from supercon2.service import _update_record, _mark_validated, _reset_record


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
                  "error_type": "extraction",
                  "authors": "D Gajda, ) A Morawski, A Zaleski, A Yamamoto, T Cetner",
                  "year": 2016}

    original_identifier = '61e136f56e3ec3a715592988'
    original_identifier_object_id = ObjectId(original_identifier)
    inserted_id = _update_record(original_identifier_object_id, new_record, mongodb.client, mongodb)

    records_by_document_after = len(list(mongodb.tabular.find({'hash': '48ba234393'})))

    assert records_by_document_after > records_by_document_before

    final_record = mongodb.tabular.find_one(inserted_id)
    assert final_record['status'] == "curated"
    assert final_record['type'] == "manual"
    assert final_record['previous'] == original_identifier_object_id
    assert str(final_record['_id']) != original_identifier
    assert final_record['error_type'] == "extraction"

    old_record_from_db = mongodb.tabular.find_one({'_id': original_identifier_object_id})

    assert old_record_from_db['status'] == "obsolete"
    assert old_record_from_db['type'] == "automatic"
    assert old_record_from_db['error_type'] == "extraction"

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
    inserted_id = _update_record(original_identifier_object_id, new_record, mongodb.client, mongodb)

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

    inserted_id = None
    with pytest.raises(Exception):
        inserted_id = _update_record(original_identifier_object_id, new_record, mongodb.client, mongodb)

    assert inserted_id is None

    records_by_document_after = len(list(mongodb.tabular.find({'hash': '48ba234393'})))
    training_data_after = len(list(mongodb.training_data.find({'hash': '48ba234393'})))

    assert records_by_document_after == records_by_document_before

    old_record_from_db = mongodb.tabular.find_one({'_id': original_identifier_object_id})

    assert old_record_from_db['status'] == "new"
    assert old_record_from_db['type'] == "automatic"
    assert 'error_type' not in old_record_from_db or old_record_from_db['error_type'] == ''

    assert training_data_after == training_data_before


def test_post_process_fields_remove_None():
    input = {"a": None, "B": "value"}
    output = post_process_fields(input, skip_none=True)

    assert list(output.keys())[0] == 'B'


def test_post_process_fields_keep_None():
    input = {"a": None, "B": "value"}
    output = post_process_fields(input, skip_none=False)

    assert list(output.keys())[0] == 'a'
    assert list(output.keys())[1] == 'B'


def test_post_process_fields_remove_trailing():
    input = {"a": "bjjab     ", "B": "value"}
    output = post_process_fields(input, remove_trailing_space=True)

    assert output['a'] == "bjjab"
    assert output['B'] == "value"


def test_post_process_fields_keep_trailing():
    input = {"a": "bjjab     ", "B": "value"}
    output = post_process_fields(input, remove_trailing_space=False)

    assert output['a'] == "bjjab     "
    assert output['B'] == "value"


def test_post_process_fields_remove_trailing_with_non_str():
    object_id = ObjectId("61e136f56e3ec3a715592988")
    input = {"a": "bjjab", "B": "value", "id": object_id, "c": None}
    output = post_process_fields(input, skip_none=True, remove_trailing_space=True)

    assert output['a'] == "bjjab"
    assert output['B'] == "value"
    assert 'c' not in output
    assert output['id'] == object_id


def test_flow_new_validated(mongodb):
    object_id = ObjectId("61e136f56e3ec3a715592988")

    object_before = mongodb.tabular.find_one({"_id": object_id})
    assert object_before['status'] == "new"
    assert object_before['type'] == "automatic"

    _mark_validated(mongodb, ObjectId("61e136f56e3ec3a715592988"))

    object_after = mongodb.tabular.find_one({"_id": object_id})
    assert object_after['status'] == "validated"
    assert object_after['type'] == "manual"


def test_flow_new_validated_reset(mongodb):
    object_id = ObjectId("61e136f56e3ec3a715592988")

    object_before = mongodb.tabular.find_one({"_id": object_id})
    assert object_before['status'] == "new"
    assert object_before['type'] == "automatic"

    _mark_validated(mongodb, ObjectId("61e136f56e3ec3a715592988"))

    object_after = mongodb.tabular.find_one({"_id": object_id})
    assert object_after['status'] == "validated"
    assert object_after['type'] == "manual"

    _reset_record(mongodb, ObjectId("61e136f56e3ec3a715592988"))

    object_after = mongodb.tabular.find_one({"_id": object_id})
    assert object_after['status'] == "new"
    assert object_after['type'] == "automatic"


def test_flow_new_validated_curated(mongodb):
    object_id = ObjectId("61e136f56e3ec3a715592988")

    object_before = mongodb.tabular.find_one({"_id": object_id})
    assert object_before['status'] == "new"
    assert object_before['type'] == "automatic"

    _mark_validated(mongodb, object_id)

    object_after = mongodb.tabular.find_one({"_id": object_id})
    assert object_after['status'] == "validated"
    assert object_after['type'] == "manual"

    new_doc = {"rawMaterial": "thin films Mg B2",
               "materialId": "-964232725",
               "formula": "Mg B2"}

    new_object_id = _update_record(object_id, new_doc, mongodb.client, mongodb)

    object_after = mongodb.tabular.find_one({"_id": new_object_id})
    assert object_after['status'] == "curated"
    assert object_after['type'] == "manual"


def test_flow_new_curated_reset(mongodb):
    object_id = ObjectId("61e136f56e3ec3a715592988")

    object_before = mongodb.tabular.find_one({"_id": object_id})
    assert object_before['status'] == "new"
    assert object_before['type'] == "automatic"

    new_doc = {"rawMaterial": "thin films Mg B2",
               "materialId": "-964232725",
               "formula": "Mg B2"}

    new_object_id = _update_record(ObjectId("61e136f56e3ec3a715592988"), new_doc, mongodb.client, mongodb)

    object_after = mongodb.tabular.find_one({"_id": new_object_id})
    assert object_after['status'] == "curated"
    assert object_after['type'] == "manual"

    _reset_record(mongodb, new_object_id)

    object_after = mongodb.tabular.find_one({"_id": new_object_id})
    assert object_after['status'] == "curated"
    assert object_after['type'] == "manual"


def test_flow_new_curated_validated_reset(mongodb):
    object_id = ObjectId("61e136f56e3ec3a715592988")

    object_before = mongodb.tabular.find_one({"_id": object_id})
    assert object_before['status'] == "new"
    assert object_before['type'] == "automatic"

    new_doc = {"rawMaterial": "thin films Mg B2",
               "materialId": "-964232725",
               "formula": "Mg B2"}

    new_object_id = _update_record(ObjectId("61e136f56e3ec3a715592988"), new_doc, mongodb.client, mongodb)

    obsolete_record = mongodb.tabular.find_one({"_id": object_id})
    assert obsolete_record['status'] == "obsolete"
    assert obsolete_record['type'] == "automatic"

    updated_record = mongodb.tabular.find_one({"_id": new_object_id})
    assert updated_record['status'] == "curated"
    assert updated_record['type'] == "manual"

    _mark_validated(mongodb, ObjectId(new_object_id))

    object_after = mongodb.tabular.find_one({"_id": new_object_id})
    assert object_after['status'] == "validated"
    assert object_after['type'] == "manual"

    _reset_record(mongodb, new_object_id)

    object_after = mongodb.tabular.find_one({"_id": new_object_id})
    assert object_after['status'] == "curated"
    assert object_after['type'] == "manual"

    obsolete_record = mongodb.tabular.find_one({"_id": object_id})
    assert obsolete_record['status'] == "obsolete"
    assert obsolete_record['type'] == "automatic"
