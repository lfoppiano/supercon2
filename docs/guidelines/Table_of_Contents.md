# Table of Contents
- Introduction
- Data description and rules
    - List of items

        |  Items related to material  |  Items related to target properties  |  Items Related to paper  |  Miscellanecus  |
        | ----  | ----  | ----   | ----  |
        |  Raw material  |  Critical Temperature  |  Document    |  Flag       |
        |  Name          |  Applied Pressure      |  DOI         |  Actions    |
        |  Formula       |  Method obtaining Tc   |  Year        |  Link Type  |
        |  Doping        |                        |  Section     |  Record Status |
        |  Variables     |                        |  Subsection  |  Error Types |
        |  Shape         |                        |  Path        |             |
        |  Substrate     |                        |  Timestamp   |             |
        |  Fabrication   |                        |  Authors     |             |
        |  Material Class |                       |  Title       |             |
        |  Crystal Structure  |                   |  Publisher   |             |
        |  Space Group   |                        |  Journal     |             |
        |  Unit cell type |                       |  Filename    |             |
        

    - Common rules to all items

        - units
        - Record status
            - Correct
            - Wrong
            - Invalid
            - missing
        - Error types
            - From table
            - Extraction
            - Linking
            - Composition resolution
        

    - Detailed description and rules for individual items        

        - Items related to material
            
            - Raw material

                - description & typical example:
                - rules for curating:

                    we do not curate this item
                

            - Name

                - description:

                    Abbrebiation of material
                    
                    for example: LSCO
                - rules for curating:
                - possible error-examples:
                

            - Formula

                - description:

                    Chemical formula of the material
                - rules for curating:
                - possible error and example:
                

            - Doping

                - description

                    Atoms and molecules that are used for doping, adjointed to the material name
                - rules for curating:
                - possible error and example
                
            
            - Variables

                - description

                    Variables that can be substituted in the formula
                - rules for curating:
                - possible error and example
                

            - Form

                - description

                    Identify the form of the material

                    for example: polycrystals, thin film, wire
                - rules for curating:
                - possible error and example
                

            - Substrate

                - description

                    Substrate on which target material is grown
                - rules for curating:
                - possible error and example
                

            - Fabrication

                - description

                    Represent all the various information that are not belonging to any of the previous tags

                    for example: annealed, irradiated

                - rules for curating:
                - possible error and example
                

            - Material Class

                - description
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
                

        

        - Items related to target property

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
                

            

        - Items related to paper

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
                

            


        - Miscellaneous

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
                

            

- Glossary
