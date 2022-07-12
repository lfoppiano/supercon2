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
| Unit cell type         |                                    | Publisher              |               |
| Space Group               |                                    | Journal                |               |
| Structure type            |                                    | Filename               |               |



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

The extraction of superconductors materials is performed, following a unified data flow. 
Failures can occur at each stage in the flow, and we distinguish each failure by naming them "error type".
Error types indicate the causes for which a specific material-properties record is invalid, wrong or missing.
Table 2 illustrates these type of errors:

| Error type             | Definition                                                                                                                                                                                                |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| From table             | When part of complete tables are incorrectly extracted, and consequently entities contained within. At the moment, table extraction is not intended and out of scope.                                                      |
| Extraction             | The entity is not extracted or its boundaries are not matching the correct information (e.g., when the entity is partially extracted or when the extraction includes text that is not part of the entity. |
| Tc classification      | The extracted temperature is not correctly classified as the target "superconductors critical temperature" (and resultantly, other temperatures were stored, such as Curie temperature, annealing temperature …)                                                                     |
| Linking                | The material is incorrectly linked to the Tc (and applied pressure if it exists) given that the entities are correctly recognised                                                                                                             |
| Composition resolution | When the exact composition cannot be resolved (e.g. the stochiometric values cannot be resolved)                                                                                                          |
<div style="text-align: center;">Table 2: List of error types, sorted by their occurrence in the data flow. </div>

### Priority between error types
figure

Following the dataflow, the priority between errors is as follows:

From table > Extraction > Tc classification > Linking > Composition resolution

This means, when a wrong formula (Extraction) is linked incorrectly (Linking) to Curie temperature (Tc classification), the error is "Extraction".


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

        The extracted material name as it is

        For example: "tetragonal Ba(Fe_1-x_Co_x_)_2_As_2_ grown on Si(111)"
    - rules for curating:

        we do not curate this item
      

- Name
    - description & typical example:

        Abbrebiation of material
          
        For example: "LSCO"
    - rules for curating:

        Try to fill when it is available

    - possible error-examples:
      

- Formula
    - description & typical example:

        Chemical formula of the material

        For example: La_1.75_Sr_0.25_CuO_4_
    - rules for curating:

        What we want is chemical formula, that ONLY consists of atomic species and numbers. Therefore;

        - When the value for $x$ in the formula can be found in the same document, try to fill it.

        - When any additional information regarding the materials remains attached (e.g. tetragonal, annealed, grown on substrate), split and put them in appropriate sections.
    - possible error-examples:

        - composition resolution:
      

- Doping
    - description & typical example:

        Atoms and molecules that are used for doping, adjointed to the material name

        For example: _Ag_-doped Bi_2_Te_3_
    - rules for curating:

        Try to fill when it is available
    - possible error and example:
      
  
- Variables
    - description & typical example:

        Variables that can be substituted in the formula
    - rules for curating:

        This is often kept unfilled, due to "composition resolution" error.  Try to fill it when curator finds it in the paper.
    - possible error-examples:
      

- Form
    - description & typical example:

        Identify the form of the material

        For example: polycrystals, thin film, wire
    - rules for curating:

        Try to fill when it is available

    - possible error and example
      

- Substrate
    - description & typical example:

        Substrate on which target material is grown

        For example: Cu grown on _Si(111)_ substrate

    - rules for curating:

        Try to fill when it is available

    - possible error and example
      

- Fabrication
    - description & typical example:

        Represent all the various information that are not belonging to any of the previous tags

        For example: annealed, irradiated

    - rules for curating:

        Try to fill when it is available

    - possible error and example
      

- Material Class
    - description & typical example:

        For the time being, class name is given by rule-based approach, based on containing either anion or cation atoms.

        For example: Fe-based

    - rules for curating:

        We do not curate this item
    - possible error-examples
      


- Unit Cell Type
    - description & typical example:

        Bravais lattice that the crystal structure of the material belongs to

        For example: tetragonal, orthorhombic
    
    - rules for curating:

        Try to fill whenever available
    - possible error-examples

        - compositional resolution
        
            Unit cell type sometimes appear as a part of "Formula".  Remove from "Formula" when it is attached.

            Example: NOTE FOR MYSELF: FILL HEHEHEHEHHEHHEHEHEHEHEHEHH

    
- Space Group
    - description & typical example:

        Space group for which the material's crystal structure belongs to.  Either No. (1-230) or "standard short symbol" is fine.

        For example: "Space group No. 225 (Fm-3m)"
    - rules for curating:
    
        try to fill whenever available
    - possible error and example


- Structure type
    - description & typical example:

        Type of crystal structure, described by the name of typical material that takes the crystal structure.

        For example: MnP-type, AlB_2_-type
    - rules for curating:
    
        Try to fill whenever available
    - possible error and example     

#### Items related to the target property

- Critical Temperature

    - description & typical example:

        Represent the value of the superconducting critical temperature, Tc. Other temperatures (fabrication conditions, etc.) should not be extracted.

        For example: 100 K

    - rules for curating:

        It has to be properly linked with composition and applied pressure(if it exists)
    - possible error-examples:
        - From table

            Note for myself fill HEHEHEHEHHEHEHEHEHEHEHEHEHEHEHEEH

        - Extraction
        
            Note for myself fill HEHEHEHEHHEHEHEHEHEHEHEHEHEHEHEEH

        - Tc classification

            Note for myself fill HEHEHEHEHHEHEHEHEHEHEHEHEHEHEHEEH

        - Linking

            Note for myself fill HEHEHEHEHHEHEHEHEHEHEHEHEHEHEHEEH

      

- Applied Pressure

    - description & typical example:

        Represent the value of applied pressure on which superconducting critical temperature Tc is determined.  Other pressures (pressure during fabrication process, etc.) should not be extracted.

        For example: 10 GPa
    - rules for curating:
    - possible error-examples:
        - Extraction

            Note for myself fill HEHEHEHEHHEHEHEHEHEHEHEHEHEHEHEEH

        - Tc classification

            Note for myself fill HEHEHEHEHHEHEHEHEHEHEHEHEHEHEHEEH

        - Linking

            Note for myself fill HEHEHEHEHHEHEHEHEHEHEHEHEHEHEHEEH
      

- Method Obtaining Tc

    - description & typical example:

        Indicates the techniques used to determine the superconductiving transition temperature, either by experimental measurements or theoretical calculations. This includes also explanatory sentences for temperature dependence of resistivity, magnetic susceptibility or specific heat graphs, not necessarily related to superconductivity.

        For example: resistivity, magnetic susceptibility, specific heat, calculated
    - rules for curating:

        Try to fill whenever available
    - possible error and example

#### Items related to the paper

- Document

    Luca please fill this
      

- DOI

    Digital Object Identifier of the paper where the entity is extracted
      

- Year
    
    Published year of the paper where the entity is extracted
      

- Section
    
    From which section the item has been extracted
      

- Subsection

    Luca please fill this
      

- Path

    Luca please fill this
      

- Timestamp

    Luca please fill this
      

- Authors

    Authors' names of the paper where the entity is extracted
      

- Title

    Title of the paper where the entity is extracted
      

- Publisher

    Publisher's name of the paper where the entity is extracted
      

- Journal

    Journal's name where the entity is extracted
      
  
- Filename

    Luca please fill this


#### Miscellaneous

- Flag
      
    Luca please fill this

- Actions

      
    Luca please fill this

- Link Type

      
    Luca please fill this

- Record Status

    described in "commmon rule" section
      

- Error Types

    described in "common rule" section

<!--
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

-->

## Glossary

This section describes the domain-specific words that are used in this document. 

| Concept    | Definition |
|------------|------------|
| SuperCon   |            |
| SuperCon 2 |            |
| Status     |            |
| Error type |            |
