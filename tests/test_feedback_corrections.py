from process.feedback_corrections import process


def test_database(mongodb):
    assert 'tabular' in mongodb.list_collection_names()
    record = mongodb.tabular.find_one({'hash': '48ba234393'})
    assert record is not None


def test_process_excel_check_obsolete_links(mongodb):
    process('tests/resources/supercon_corrected.xlsx', mongodb)

    tabular_collection = mongodb.get_collection("tabular")
    records_all = tabular_collection.find({"hash": "48ba234393"})
    assert records_all.count() == 6

    records_manually_corrected = list(
        tabular_collection.find({"hash": "48ba234393", "status": "valid", "type": "manual"}))
    assert len(records_manually_corrected) == 2

    for record_manually_corrected in records_manually_corrected:
        assert tabular_collection.find_one({"_id": record_manually_corrected['previous']})["status"] == "obsolete"

    records_obsolete = list(tabular_collection.find({"hash": "48ba234393", "status": "obsolete"}))
    assert len(records_obsolete) == 2


def test_process_excel_verify_training_data(mongodb):
    process('tests/resources/supercon_corrected.xlsx', mongodb)
    tabular_collection = mongodb.get_collection("tabular")
    corrected_identifiers = [str(record['_id']) for record in
                             tabular_collection.find({"status": "valid", "type": "manual"}, {'_id': 1})]

    training_data_collection = mongodb.get_collection("training-data")
    assert len(list(training_data_collection)) == 2

    training_data_records = list(training_data_collection.find())

    assert str(training_data_records[0]['corrected_record_id']) in corrected_identifiers
    assert training_data_records[0]['hash'] == "48ba234393"

    assert str(training_data_records[1]['corrected_record_id']) in corrected_identifiers
    assert training_data_records[1]['hash'] == "48ba234393"
