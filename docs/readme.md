# Technical documentation

## Introduction

## Overview 


## Workflow status flags

The workflows flags are properties within the database that are used to mark different status of the data:
 - `type` indicate the type of operation that was performed
 - `status` indicate the status of the current record

and their value is used as follow:

| Name  | Values            | Description |
|-------|-------------------|-------------|
| type | manual | The performed operation was manual  |
| type | automatic | The performed operation was automatic (anomaly detection, loading script)  |
| status | valid | The record is valid (if `type=automatic`, might still be wrong) |
| status | invalid | The record is invalid, incorrect (the certanly depends on the `type` value |
| status | obsolete | The record is obsolete, a new record supersedes it and the new record will point to the old (if we assume that a correction will create new record) |
| status | empty | The record does not contains any information (when the document does not have any link) 

However, the flags should be used in pair and the state change is illustrate as follows: 

![](images/status-flags-schema.png)

