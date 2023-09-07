#### Training data management

This section provides an overview of the collected training data.
We follow the idea that exploiting corrections for training data is an important feature to provide improvement of the data quality and model accuracy.
Therefore, when a record is corrected, its original sentence, tokens and annotaions are stored in a separate space and can be sent to label-studio, which is a tool for managing annotations.

The training data management looks like the following image:

![](docs/images/training-data-viewer.jpg)

Each row represent one training item.

The `status` indicate:
- `new` if the training data has been added but not yet sent to label-studio
- `in progress` if the training data was sent to label-studio

**NOTE** if two materials within the same sentence are corrected, the sentence will appear twice in the training data management. For this reason the data shall be selectively sent to label-studio.

The `actions` column comprises two action-buttons:
- `send` the training data to label-studio
- `remove` the training data, in case of duplicates. **In general is always better to keep the training data even if they have been sent to label-studio already**
