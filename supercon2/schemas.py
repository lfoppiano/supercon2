from flask_marshmallow import Schema
from marshmallow.fields import String, List, Field, Integer, DateTime
from marshmallow.validate import OneOf


class Flag(Schema):
    status = String()
    type = String()


class RecordParamsIn(Schema):
    type = String(default="automatic", validate=OneOf(['manual', 'automatic']))
    status = String(default=None, validate=OneOf(['valid', 'invalid']))
    document = String(default=None)
    publisher = String(default=None)
    year = Integer(default=None)
    start = Integer(default=0)
    limit = Integer(default=-1)


class UpdatedRecord(Schema):
    previous_id = String(default=None)
    id = String()
    description = String(default=None)


class Record(Schema):
    id = String()
    rawMaterial = String()
    materialId = String(allow_none=True)
    name = String(allow_none=True)
    formula = String(allow_none=True)
    doping = String(allow_none=True)
    materialClass = String(allow_none=True)
    fabrication = String(allow_none=True)
    shape = String(allow_none=True)
    substrate = String(allow_none=True)
    variables = String(allow_none=True)
    unitCellType = String(allow_none=True)
    unitCellTypeId = String(allow_none=True)
    spaceGroup = String(allow_none=True)
    spaceGroupId = String(allow_none=True)
    crystalStructure = String(allow_none=True)
    crystalStructureId = String(allow_none=True)
    criticalTemperature = String()
    criticalTemperatureId = String(allow_none=True)
    criticalTemperatureMeasurementMethod = String(allow_none=True)
    criticalTemperatureMeasurementMethodId = String(allow_none=True)
    appliedPressure = String(allow_none=True)
    appliedPressureId = String(allow_none=True)
    linkType = String(allow_none=True)
    section = String(allow_none=True)
    subsection = String(allow_none=True)
    sentence = String(allow_none=True)
    sentence_decorated = String(allow_none=True)
    path = String(allow_none=True)
    filename = String(allow_none=True)
    hash = String()
    type = String()
    timestamp = DateTime(allow_none=True)
    status = String()
    title = String(allow_none=True)
    doi = String(allow_none=True)
    authors = String(allow_none=True)
    publisher = String(allow_none=True)
    journal = String(allow_none=True)
    year = String(allow_none=True)
    error_type = String(allow_none=True)


class Publishers(Schema):
    publishers = List(Field)


class Years(Schema):
    years = List(Field)


# class Journals(Schema):
#     journals = List(Field)


# class ErrorTypes(Dict):
#     error_types = Dict(keys=String(), values=String())
