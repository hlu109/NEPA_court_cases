Data/
├── Raw/
│   ├── CourtListener metadata/
│   │   └── run_<YYYYMMDD_HHMMSS>/    # CourtListener raw data
│   │       ├── cluster_metadata.csv
│   │       ├── docket_metadata.csv
│   │       └── opinion_metadata.csv
│   ├── nepa_judicial/
│   │   └── data/
│   │       └── NEPA Lit Circuit WL Sample-Combo Supp-Coded Final 2001-15 2.7.24.xlsx    # this is AdelGlicks raw; the Excel sheet name to read is "NEPA Circuit Data"
│   └── Breakthrough_NEPA_Cases_2013_2022.csv    # Breakthrough raw data
├── Intermediate/
│   ├── Cleaned Datasets/
│   │   ├── AdelGlicks.csv
│   │   ├── Breakthrough.csv
│   │   └── CourtListener/
│   │       ├── cluster_metadata.csv   # with mapping to lead opinion id
│   │       ├── opinion_metadata.csv
│   │       └── docker_metadata.csv
│   ├── CourtListener_AdelGlicks_merged_ids.csv
│   ├── CourtListener_AdelGlicks_merged_ids_w_assignment.csv
│   ├── Outcome Coding Assignments/
│   │   ├── train.csv
│   │   ├── val.csv
│   │   ├── test.csv
│   │   └── CourtListener_all.csv
│   ├── Outcome Coding Predictions/
│   │   ├── train.csv
│   │   └── val.csv
│   ├── Outcome Coding True/
│   │   ├── val.csv
│   │   └── test.csv
│   └── Outcome Coding Final/
│       └── CourtListener_all.csv
