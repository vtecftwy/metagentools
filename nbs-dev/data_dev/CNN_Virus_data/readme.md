### CNN Virus data

This directory includes data used to train and validate the initial CNN Virus model, as well as a few smaller datasets for experimenting. 


#### File list and description:
##### 50-mer 
50-mer reads and their labels, in *text format* with one line per sample. Each line consists of three components, separated by tabs: the 50-mer read or sequence, the virus species label and the position label:
```text
'TTACNAGCTCCAGTCTAAGATTGTAACTGGCCTTTTTAAAGATTGCTCTA    94    5\n'
``` 
Files:
- `50mer_training`: dataset with 50,903,296 reads for training
- `50mer_validating`: dataset with 1,000,000 reads for validation
- `50mer_ds_100_reads`: small subset of 100 reads from the validating dataset for experiments

##### 150-mer
150-mer reads and their labels in *text format* in a similar format as above:
```text
'TTCTTTCACCACCACAACCAGTCGGCCGTGGAGAGGCGTCGCCGCGTCTCGTTCGTCGAGGCCGATCGACTGCCGCATGAGAGCGGGTGGTATTCTTCCGAAGACGACGGAGACCGGGACGGTGATGAGGAAACTGGAGAGAGCCACAAC    6    0\n'
```
Files:
- `ICTV_150mer_benchmarking`: dataset with 10,0000 read
- `150mer_ds_100_reads`: small subset of 100 reads from `ICTV_150mer_benchmarking`

##### Longer reads
Reads of various length with no labels, in simple *fasta format*. Each read sequence is preceded by a definition line: `> Sequence n`, where `n` is the sequence number.

Files:
- `training_sequences_300bp.fasta`: dataset with 9,000 300-mer reads
- `training_sequences_500bp.fasta`: dataset with 9,000 500-mer reads
- `validation_sequences.fasta`: dataset with 564 reads of mixed lengths ranging from 163-mer to 497-mer

##### Other files:
- `virus_name_mapping`: mapping between virus species and their numerical label
- `weight_of_classes`:  weights for each virus species class in the training dataset

