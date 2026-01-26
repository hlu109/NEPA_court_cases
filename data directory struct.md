Data/
├── Raw/
│   ├── CourtListener metadata/
│   │   └── run_<YYYYMMDD_HHMMSS>/    # CourtListener raw data (timestamped runs)
│   │       ├── cluster_metadata.csv
│   │       ├── docket_metadata.csv
│   │       ├── opinion_metadata.csv
│   │       ├── complete_metadata.json
│   │       └── log.txt
│   ├── Adelman Glicksman/
│   │   └── data/
│   │       └── NEPA Lit Circuit WL Sample-Combo Supp-Coded Final 2001-15 2.7.24.xlsx
│   │           # Excel sheet name: "NEPA Circuit Data"
│   └── Breakthrough_NEPA_Cases_2013_2022.csv    # Breakthrough raw data
├── Intermediate/
│   ├── Cleaned Datasets/
│   │   ├── AdelGlicks.csv
│   │   ├── Breakthrough.csv
│   │   └── CourtListener/
│   │       ├── cluster_metadata.csv   # with mapping to lead opinion id
│   ├── Docket Matching/
│   │   ├── CL_AG_match_stats.txt
│   │   ├── CL_AG_matching.csv
│   │   └── CL_AG_matched_val_test_assignments.csv
│   ├── Outcome Coding Assignments/
│   │   ├── AG_val.csv
│   │   ├── AG_test.csv
│   │   └── CL_train.csv
│   ├── Outcome Coding Predictions/
│   │   ├── courtlistener_metadata_with_LLM_outcomes.csv   # contains metadata for all CourtListener cases merged with LLM coding of lead opinion outcomes 
│   │   ├── LLM_opinion_coding.csv                         # contains just opinion coding without CourtListener metadata
│   │   ├── AG_val_predictions.csv                         # contains case outcomes for validation subset
│   │   └── CL_train_predictions.csv                       # contains case outcomes for non-val/test subset 
│   ├── Outcome Coding Eval/
│   │   ├── val_performance.csv
│   │   ├── [various confusion matrices]
│   │   └── (test_performance.csv --- eventually) 
│   ├── Summary Statistics/
│   │   └── llm_opinion_coding_frequencies.csv
│   └── gemini_output/
│       └── opinions_<download_run_timestamp>_coding_<LLM_run_timestamp>/
│           └── opinions_<download_run_timestamp>_coding_<LLM_run_timestamp>.csv
