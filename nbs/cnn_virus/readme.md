# Reference pipelines for CNN Virus project

## Introduction
This page summarize the reference pipelines we have defined and tested during the CNN Virus project. Each pipeline is defined and described in one or several Jupyter Notebook(s) (`ref_n.nn_description.ipynb`). When spread over several notebooks, the pipelines must be run in a specific order, as they build on each other. Each notebook will indicate at the start which other notebook come before it.

Each pipeline is applied to one set of data, inference or training and analysis.

## 1. CNN Virus Original Training and Testing Data
Pipelines in this section are defined to use the original training and testing data provided by the CNN Virus project, i.e.:
- `data/CNN_Virus_data/50mer_training`
- `data/CNN_Virus_data/50mer_validating`

All data are based on 50-mer reads.

### Inference using original data [(nb ref 1.10)](ref_1.10_infer_w_orig_data.ipynb)
??? add description here

### Inference and Analysis [(nb ref 1.11)](ref_1.11_infer_w_orig_data_and_analysis.ipynb)
??? add description here


## 2. NCBI CoV Reference Sequences
All nbs are in WIP status.

## 3. Real CoV Reference Sequence
All nbs are in WIP status.

## 4. NCBI YFV Reference Sequences
### Reference sequence preprocessing [(nb ref 4.01)](ref_4.01_yf_ncbi_data_preproc_pipeline.ipynb)
Pre-process the original YFV reference sequence file into the format required by the CNN Virus project.

### Inference on selected refseqs (local storage) [(nb ref 4.11)](ref_4.11_yf_ncbi_inference_local_selected_refseqs.ipynb)

Use CNN Virus model to infer labels for YFV reads from a selection of the YFV reference sequences.

### Inference on selected refseqs (sqlite storage) [(nb ref 4.12)](ref_4.12_yf_ncbi_inference_sqlite.ipynb)
Use CNN Virus model to infer labels for YFV reads from a selection of the YFV reference sequences, and save detailed inference results for each read into a sqlite database for further analysis.

### Inference on all refseqs (local storage)[(nb ref 4.13)](ref_4.13_yf_ncbi_inference_local_all_refseqs.ipynb)
Use CNN Virus model to infer labels for YFV reads from a selection of the YFV reference sequences, and save shorter inference report on inference result for each read in a `csv` file for further analysis.
### Analysis from local storage (3bp) [(nb ref 4.20)](ref_4.20_yf_ncbi_analysis_3bp_local.ipynb)
Use inference report from [preprocessing](ref_4.20_yf_ncbi_analysis_3bp_local.ipynb) and perform following analysis:
- ???
- Impact of position in reference sequence on inference results, with a resolutuion of 3 base pairs.

### Build refseq selection list [(nb ref 4.80)](ref_4.80_yf_ncbi_select_refseqs.ipynb)
Build a list of YFV reference sequences to be used for inference, based on their presence or not in the available distance matrix.

## Others
