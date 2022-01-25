# Technical documentation

## Workflow status flags

The workflows flags are properties within the database that are used to mark different status of the data:
 - `type` indicate the type of operation that was performed
 - `status` indicate the status of the current record 

(if we assume that a correction will create new record)

The current version works using the following flags:

| Name  | Values            | Description |
|-------|-------------------|-------------|
| type | manual | The performed operation was manual  |
| type | automatic | The performed operation was automatic (anomaly detection, loading script)  |
| status | valid | The record is valid |
| status | invalid | The record is invalid |
| status | obsolete | The record is obsolete, a new record superseeds this one |
| status | empty | The record does not contains any information (when the document does not have any link) 

However the flags should be used in pair and the state change is illustrate as follows: 

![](images/status-flags-schema.png)
