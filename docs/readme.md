# Technical documentation

## Workflow status flags

The workflows flags are properties within the database that are used to mark different status of the data.

The current version works using the following flags:

| Name  | Values            | Description |
|-------|-------------------|-------------|
| type | manual, automatic | how the operation was performed |
| status | valid, invalid, obsolete | (if we assume that a correction will create new record) |

below we illustrate their use: 

![](images/status-flags-schema.png)