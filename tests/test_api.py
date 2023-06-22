from unittest.mock import MagicMock

import pytest
from _pytest.outcomes import fail
from bson import ObjectId

from commons.correction_utils import post_process_fields
from supercon2 import service
from supercon2.service import _update_record, mark_record_validated, _mark_validated, _reset_record, delete_record, \
    _delete_record, get_records, get_record, validate_objectId


def test_get_records_should_compute_query(mongodb):
    assert 'tabular' in mongodb.list_collection_names()

    def new_connect_and_get_db():
        return mongodb

    service.connect_and_get_db = new_connect_and_get_db

    records = get_records()
    assert len(records) == 4

    records = get_records(status="new")
    assert len(records) == 3

    records = get_records(status="curated")
    assert len(records) == 1

    records = get_records(document="48ba234394")
    assert len(records) == 1

    records = get_records(document="48ba234393")
    assert len(records) == 3


def test_validate_objectId():
    object_id = validate_objectId("61e136f56e3ec3a715592988")

    assert object_id is not None


def test_validate_objectId_should_fail():
    with pytest.raises(Exception) as exc_info:
        validate_objectId("bao")



# def test_get_record_should_compute_query(mongodb):
#     assert 'tabular' in mongodb.list_collection_names()
#
#     def new_connect_and_get_db():
#         return mongodb
#
#     service.connect_and_get_db = new_connect_and_get_db
#
#     record = get_record(id="61e136f56e3ec3a715592988")
#
#     assert record is not None

