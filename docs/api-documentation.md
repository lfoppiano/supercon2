# API documentation

The application supports custom `root_path`, which can be configured from the `config.yaml` file. All the API is served
under the custom `root_path`.

The API documentation is provided by apiflask OpenAPI (swagger) implementation.

| URL       | Description                                    |
|-----------|------------------------------------------------|
| `/spec`   | Serve the OpenAPI documentation as YAML        |
| `/redoc`  | Serve the OpenAPI documentation via redoc      |
| `/docs`   | Serve the OpenAPI documentation via swagger-UI |

Following an API documentation summary:

| URL                                                     | Method     | Description                                                                      |
|---------------------------------------------------------|------------|----------------------------------------------------------------------------------|
| `/annotation/<doc_id>`                                  | GET        | Return the JSON annotation representation of a document                          |
| `/biblio/<doc_id>`                                      | GET        | Get the bibliographic data of the document by document id                        |
| `/config`                                               | GET        | Get the configuration                                                            |
| `/database`                                             | GET        | Render the database interface                                                    |
| `/database/document/<doc_id>`                           | GET        | Get the tabular data filtering by doc_id                                         |
| `/document/<doc_id>`                                    | GET        | Render the PDF viewer (PDF document + JSON annotations)                          |
| `/label/studio/project/{project_id} `                   | GET        | Get information from a label-studio project                                      |
| `/label/studio/project/{project_id}/record/{record_id}` | POST/PUT   | Send annotation task to Label studio                                             |
| `/label/studio/project/{project_id}/records`            | POST/PUT   | Send all annotation tasks to Label studio                                        |
| `/label/studio/projects  `                              | GET        | Get the list of projects from label-studio (annotation tool)                     |
| `/pdf/<doc_id>`                                         | GET        | Return the PDF document corresponding to the identifier                          |
| `/publishers`                                           | GET        | Get list of all publishers in the database                                       |
| `/record`                                               | POST       | Create a new record                                                              |  
| `/record/<record_id>`                                   | DELETE     | Remove a record by its id                                                        |  
| `/record/<record_id>`                                   | GET        | Return the single record                                                         |  
| `/record/<record_id>`                                   | PUT/PATCH  | Update the record                                                                |  
| `/record/<record_id>/mark_invalid`                      | PUT/PATCH  | Mark a record as invalid                                                         |  
| `/record/<record_id>/mark_validated`                    | PUT/PATCH  | Mark a record as validated                                                       |  
| `/record/<record_id>/reset`                             | PUT/PATCH  | Reset record status                                                              |  
| `/record/<record_id>/status`                            | GET        | Return the flags of a single record                                              | 
| `/records`                                              | GET        | Return the list of records                                                       |
| `/records/<type>`                                       | GET        | Return the list of records of a specific type `automatic`/`manual`               |
| `/records/<type>/<publisher>/<year>`                    | GET        | Return the list of records of a specific type + publisher + year                 |
| `/records/<type>/<year>`                                | GET        | Return the list of records of a specific type + year                             |
| `/stats`                                                | GET        | Return statistics                                                                |
| `/training/data`                                        | GET        | Get the list of all training data stored in the database                         |
| `/training/data/status/<status>`                        | GET        | Get the training data by status (of the training data: new, exported, corrected) |
| `/training/data/<training_data_id>`                     | GET        | Export training data                                                             |
| `/training/data/<training_data_id>`                     | DELETE     | Remove training data                                                             |
| `/training_data`                                        | GET        | Render interface for managing the training data                                  |
| `/version`                                              | GET        | Render interface for managing the training data                                  |
| `/years`                                                | GET        | Render interface for managing the training data                                  |
