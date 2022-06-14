# Guideline for data correction

## Table of Contents

* [Introduction](#introduction)
* [Data model](#data-model)
  + [Data description](#data-description)
  + [List of items](#list-of-items)
  + [Common rules to all items](#common-rules-to-all-items)
* [General principles](#general-principles)
   + [Units](#units)
   + [Record status](#record-status)
   + [Error types](#error-types)
* [Rules](#rules)
   + [Detailed description and rules for individual items](#detailed-description-and-rules-for-individual-items)
     + [Item related to materials](#items-related-to-material)
     + [Item related to the target property](#items-related-to-the-target-property)
     + [Item related to the paper](#items-related-to-the-paper)
     + [Miscellaneous](#miscellaneous)
   + [Examples](#examples)
     + [Missing entities](#missing-entity) 
     + [Invalid temperature](#invalid-temperature) 
     + [Composition extraction](#composition-extraction) 
* [Glossary](#glossary)


## Introduction

This document describes the general principles and rules to follow to amend the data of the Supercon 2 database. 
SuperCon 2 is a database of superconducting materials which properties are extracted automatically from scientific literature.

The guidelines assume that the user knows well the SuperCon 2 application. The documentation on how to use SuperCon 2 is in ...

## Data Model
This section describes the different information that is stored in the database. 

### Data description

#### List of items

| Items related to material | Items related to target properties | Items Related to paper | Miscellanecus |
|---------------------------|------------------------------------|------------------------|---------------|
| Raw material              | Critical Temperature               | Document               | Flag          |
| Name                      | Applied Pressure                   | DOI                    | Actions       |
| Formula                   | Method obtaining Tc                | Year                   | Link Type     |
| Doping                    |                                    | Section                | Record Status |
| Variables                 |                                    | Subsection             | Error Types   |
| Form                     |                                    | Path                   |               |
| Substrate                 |                                    | Timestamp              |               |
| Fabrication               |                                    | Authors                |               |
| Material Class            |                                    | Title                  |               |
| Crystal Structure         |                                    | Publisher              |               |
| Space Group               |                                    | Journal                |               |
| Unit cell type            |                                    | Filename               |               |



## General principles

In this section, we illustrate the general principles that are applied to the guidelines. 
Both "Record status" and "Error types" will be covered in [Rules](#rules) with examples and illustration.

### Units

As a general rule the Units are kept in the data. Although GPa and K are the most common units for `applied pressure` and `superconducting critical temperature`, there are still several cases of valid papers mentioning other units, e.g., `kbar` or `MPa`. 

### Record status

These are concepts. Add the status flow. 

| Status  | Definition                                                                     |
|---------|--------------------------------------------------------------------------------|
| correct | when the record (extracted data and linking) is correct                        |
| wrong   | when some aspects of the records are incorrect                                 |
| invalid | when the record is not a SC record and it should be removed from the database  |
| missing | if the record was not extracted                                                |
<div style="text-align: center;">Table 1: A record can be marked with four status type. </div>

### Error types

The extraction of superconductors materials follows a precise data flow. 
However, failures can occur at any time in the flow and it is important to know at which point they occur.
In other words, the error type indicates the causes for which a specific material-properties record is invalid, wrong or missing.
Table 2 illustrates these type of errors:

| Error type             | Definition                                                                                                                                                                                                |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| From table             | When part of complete tables are incorrectly extracted, and consequently entities contained within. At the moment, table extraction is not performed.                                                      |
| Extraction             | The entity is not extracted or its boundaries are not matching the correct information (e.g., when the entity is partially extracted or when the extraction includes text that is not part of the entity. |
| Tc classification      | The temperature is not correctly classified as "superconductors critical temperature" (e.g. Curie temperature, Magnetic temperature…)                                                                     |
| Linking                | The material is incorrectly linked to the Tc given that the entities are correctly recognised                                                                                                             |
| Composition resolution | When the exact composition cannot be resolved (e.g. the stochiometric values cannot be resolved)                                                                                                          |
<div style="text-align: center;">Table 2: List of error types, sorted by their occurrence in the data flow. </div>


## Rules

There are two types of actions that a curator can do when checking the data:  

1. Data reporting or flagging
2. Data correction

The (1) data reporting (or flagging) is the process in which a record is marked as "possibly invalid". 
The term "flag" indicates the action of adding a flag on top of a record. In this case, the record will be hidden from the public view of the database. 
In addition, curators could select only reported records and inspect them thoughtfully, amending or removing for good (2). 


### Detailed description and rules for individual items        

#### Items related to material
            
- Raw material
    - description & typical example:
    - rules for curating:

        we do not curate this item
      

- Name
    - description & typical example:

        Abbrebiation of material
          
        For example: LSCO
    - rules for curating:
    - possible error-examples:
      

- Formula
    - description & typical example:

        Chemical formula of the material
    - rules for curating:
    - possible error and example:
      

- Doping
    - description & typical example:

        Atoms and molecules that are used for doping, adjointed to the material name
        For example: _Ag_-doped Bi2Te3
    - rules for curating:
    - possible error and example:
      
  
- Variables
    - description

        Variables that can be substituted in the formula
    - rules for curating:

        This is often kept unfilled, due to "composition resolution" error.  Try to fill it when curator finds it in the paper.
    - possible error and example:
      

- Form
    - description

        Identify the form of the material

        for example: polycrystals, thin film, wire
    - rules for curating:
    - possible error and example
      

- Substrate
    - description

        Substrate on which target material is grown

        For example: Cu grown on _Si(111)_ substrate

    - rules for curating:
    - possible error and example
      

- Fabrication
    - description

        Represent all the various information that are not belonging to any of the previous tags

        For example: annealed, irradiated

    - rules for curating:
    - possible error and example
      

- Material Class
    - description

        For the time being, class name is given by rule-based approach, based on containing either anion or cation atoms.

        Fe-based

    - rules for curating:
    - possible error and example
      

- Crystal Structure
    - description
    - rules for curating:
        try to fill whenever available
    - possible error and example
      

- Space Group
    - description
    - rules for curating:
        try to fill whenever available
    - possible error and example
      

- Unit Cell Type
    - description

#### Items related to the target property

- Critical Temperature

    - description

    Represent the value of the superconducting critical temperature, Tc. Other temperatures (fabrication conditions, etc.) should not be extracted.
    - rules for curating:
        It has to be properly linked with composition and applied pressure(if it exists)
    - possible error and example
        There could be "Failure in extraction" and "Link failure".
        - Failure in extraction

      

- Applied Pressure

    - description

    Represent the value of applied pressure on which superconducting critical temperature Tc is determined.  Other pressures (pressure during fabrication process, etc.) should not be extracted.
    - rules for curating:
    - possible error and example
      

- Method Obtaining Tc

    - description:

        Indicates the techniques used to determine the superconductiving transition temperature, either by experimental measurements or theoretical calculations. This includes also the study of temperature/resistivity, temperature/magnetic field graphs, not necessarily related to superconductivity (what does this mean?).
    - rules for curating::
    - possible error and example

#### Items related to the paper

- Document

    - description
        Document ID of the paper
      

- DOI

    - description
        Digital Object Identifier of the paper
      

- Year

    - description
        Published year of the paper
      

- Section

    - description
        From which section the item has been extracted
      

- Subsection

    - description
      

- Path

    - description
      

- Timestamp

    - description
      

- Authors

    - description
      

- Title

    - description
      

- Publisher

    - description
      

- Journal

    - description
      
  
- Filename

    - description

#### Miscellaneous

- Flag
    - description
      

- Actions
    - description
      

- Link Type
    - description
      

- Record Status
    described in "commmon rule" section
      

- Error Types
    described in "common rule" section


### Examples

#### Missing entity

In the following example the entity has been missed completely. In this case the cause is likely "Extraction" because the process failed to recognise `HCl`. 

![](images/example-wrong-missing-entity.jpg)
<div style="text-align: center;">Figure 1: Example of missing entity. </div>


#### Invalid temperature 
In the following example the temperature of about 1234 K has been extracted. This case is likely a problem of Tc classification because the temperature should not have classified as `superconductor critical temperature` and therefore not linked. 

![](images/example-wrong-synthetised-temperature.jpg)
<div style="text-align: center;">Figure 2: Example of invalid extracted temperature. </div>

#### Composition extraction 
[LF] This specific case should be clarified [Ref](https://github.com/lfoppiano/supercon2/issues/71#issuecomment-1098751198)

![](images/example-wrong-composition-recognition.jpg)
<div style="text-align: center;">Figure 3: Example </div>


## Glossary

This section describes the domain-specific words that are used in this document. 

| Concept    | Definition |
|------------|------------|
| SuperCon   |            |
| SuperCon 2 |            |
| Status     |            |
| Error type |            |
