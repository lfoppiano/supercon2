from flask_marshmallow import Schema
from marshmallow.fields import String, List, Field

class Flag(Schema):
    status = String()
    type = String()

# class Records(Schema):


class Record(Schema):
    id = String()
    rawMaterial = String()
    materialId = String()
    name = String()
    formula = String()
    doping = String()
    materialClass = String()
    fabrication = String()
    substrate = String()
    variables = String()
    unitCellType = String()
    unitCellTypeId = String()
    spaceGroup = String()
    spaceGroupId = String()
    crystalStructure = String()
    crystalStructureId = String()
    criticalTemperature = String()
    criticalTemperatureId = String()
    criticalTemperatureMeasurementMethod = String()
    criticalTemperatureMeasurementMethodId = String()
    appliedPressure = String()
    appliedPressureId = String()
    linkType = String()
    section = String()
    subsection = String()
    sentence = String()
    path = String()
    filename = String()
    hash = String()
    type = String()
    timestamp = String()
    status = String()
    title = String()
    doi = String()
    authors = String()
    publisher = String()
    journal = String()
    year = String()


class Publishers(Schema):
    publishers = List(Field)


class Years(Schema):
    years = List(Field)


class Journals(Schema):
    journals = List(Field)
