### Data structure for `metagentools`
This directory includes all the data required for the project `metagentools`.

```text
data
 |--- CNN_Virus_data 
 |--- ncbi           
 |--- ncov_data      
 |--- saved         
 |--- ....           
     
```
#### Sub-directories
- `CNN_Virus_data`: includes all the data related to the original CNN Virus paper, i.e. training data and validation data in a format that can be used by the CNN Virus code.
- `ncbi`: includes data related to the use of CoV sequences from NCBI: reference sequences, simulated reads, inference datasets, inference results.
- `ncov_data`: includes data related to the use of non Cov sequences from various sources: reference sequences, simulated reads, inference datasets, inference results.
- `saved`: includes model saved parameters and preprocessing datasets.
