### Data structure for `metagentools`
This directory includes all the data required for the project `metagentools`.

```text
data
 |--- CNN_Virus_data 
 |--- ncbi                
 |--- saved         
 |--- yf-reads
 |--- ....           
     
```
#### Sub-directories
- `CNN_Virus_data`: includes all the data related to the original CNN Virus paper, i.e. training data and validation data in a format that can be used by the CNN Virus code.
- `ncbi`: includes data related to the use of viral sequences from NCBI: reference sequences, simulated reads, inference datasets, inference results.
- `saved`: includes model saved parameters and preprocessing datasets.
- `yf-reads`: includes all data related to real yellow fever reads, from "wet" samples

Also available on AWS S3 at `https://s3.ap-southeast-1.amazonaws.com/bio.cnn-virus.data/data/...`