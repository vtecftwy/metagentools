# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs-dev/03_cnn_virus_data.ipynb.

# %% auto 0
__all__ = ['FastaFileReader', 'FastqFileReader', 'AlnFileReader', 'create_infer_ds_from_fastq', 'strings_to_tensors']

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 3
from ecutilities.core import validate_path
from functools import partial, partialmethod
from ..bio import q_score2prob_error
from ..core import TextFileBaseReader, JsonFileReader
from pathlib import Path
from typing import Any, Optional

import json
import numpy as np
import re
import tensorflow as tf
import warnings

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 26
class FastaFileReader(TextFileBaseReader):
    """Wrap a FASTA file and retrieve its content in raw format and parsed format"""
    def __init__(
        self,
        path: str|Path,  # path to the Fasta file
    ):
        super().__init__(path, nlines=1)
        # self.parsing_rules_json = Path('../default_parsing_rules.json').resolve()
        self.text_to_parse_key = 'definition line'
        self.set_parsing_rules(verbose=False)
        
    def __next__(self)-> dict[str, str]:   # `{'definition line': text in dfn line, 'sequence': full sequence as str}` 
        """Return one definition line and the corresponding sequence"""
        lines = []
        for i in range(2):
            lines.append(self._safe_readline())
        dfn_line = lines[0]
        sequence = lines[1].replace('\n', '')
        return {'definition line':dfn_line, 'sequence':f"{sequence}"}
    
    def print_first_chunks(
        self, 
        nchunks:int=3,  # number of chunks to print out
    ):
        """Print the first `nchunks` chunks of text from the file"""
        self.reset_iterator()
        for i, seq_dict in enumerate(self.__iter__()):
            print(f"\nSequence {i+1}:")
            print(seq_dict['definition line'])
            print(f"{seq_dict['sequence'][:80]} ...")
            if i >= nchunks: break
        self.reset_iterator()
            
    def parse_file(
        self,
        add_seq :bool=False,     # When True, add the full sequence to the parsed metadata dictionary
        save_json: bool=False    # When True, save the file metadata as a json file of same stem name
    )-> dict[str]:               # Metadata as Key/Values pairs
        """Read fasta file and return a dictionary with definition line metadata and optionally sequences"""
    
        self.reset_iterator()
        parsed = {}
        for d in self:
            dfn_line = d['definition line']
            seq = d['sequence']
            metadata = self._parse_text_fn(dfn_line, self.re_pattern, self.re_keys)
            if add_seq: metadata['sequence'] = seq         
            parsed[metadata['seqid']] = metadata
                        
        if save_json:
            p2json = self.path.parent / f"{self.path.stem}_metadata.json"
            with open(p2json, 'w') as fp:
                json.dump(parsed, fp, indent=4)
                print(f"Metadata for '{self.path.name}'> saved as <{p2json.name}> in  \n{p2json.parent.absolute()}\n")

        return parsed

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 70
class FastqFileReader(TextFileBaseReader):
    """Iterator going through a fastq file's sequences and return each section + prob error as a dict"""
    def __init__(
        self,
        path:str|Path,   # path to the fastq file
    )-> dict:           # key/value with keys: definition line; sequence; q score; prob error
        self.nlines = 4
        super().__init__(path, nlines=self.nlines)
        self.text_to_parse_key = 'definition line'
        self.set_parsing_rules(verbose=False)        
    
    def __next__(self):
        """Return definition line, sequence and quality scores"""
        lines = []
        for i in range(self.nlines):
            lines.append(self._safe_readline().replace('\n', ''))
        
        output = {
            'definition line':lines[0], 
            'sequence':f"{lines[1]}", 
            'read_qscores': f"{lines[3]}",
        }
        output['probs error'] = np.array([q_score2prob_error(q) for q in output['read_qscores']])
        
        return output
    
    def print_first_chunks(
        self, 
        nchunks:int=3,  # number of chunks to print out
    ):
        """Print the first `nchunks` chunks of text from the file"""
        for i, seq_dict in enumerate(self.__iter__()):
            print(f"\nSequence {i+1}:")
            print(seq_dict['definition line'])
            print(f"{seq_dict['sequence'][:80]} ...")
            if i >= nchunks: break
            
    def parse_file(
        self,
        add_readseq :bool=False,    # When True, add the full sequence to the parsed metadata dictionary
        add_qscores:bool=False,     # Add the read ASCII Q Scores to the parsed dictionary when True
        add_probs_error:bool=False, # Add the read probability of error to the parsed dictionary when True
        save_json: bool=False       # When True, save the file metadata as a json file of same stem name
    )-> dict[str]:                  # Metadata as Key/Values pairs
        """Read fastq file, return a dict with definition line metadata and optionally read sequence and q scores, ..."""
    
        self.reset_iterator()
        parsed = {}
        for d in self:
            dfn_line = d['definition line']
            seq, q_scores, prob_e = d['sequence'], d['read_qscores'], d['probs error']
            metadata = self._parse_text_fn(dfn_line, self.re_pattern, self.re_keys)
            if add_readseq: metadata['readseq'] = seq         
            if add_qscores: metadata['read_qscores'] = q_scores
            if add_probs_error: metadata['probs error'] = prob_e
            parsed[metadata['readid']] = metadata 
                        
        if save_json:
            p2json = self.path.parent / f"{self.path.stem}_metadata.json"
            with open(p2json, 'w') as fp:
                json.dump(parsed, fp, indent=4)
                print(f"Metadata for '{self.path.name}'> saved as <{p2json.name}> in  \n{p2json.parent.absolute()}\n")

        return parsed

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 85
class AlnFileReader(TextFileBaseReader):
    """Iterator going through an ALN file"""
    def __init__(
        self,
        path:str|Path,   # path to the aln file
    )-> dict:            # key/value with keys: 
        self.nlines = 1
        super().__init__(path, nlines=self.nlines)
        self.header = self.read_header()
        self.nlines = 3
        self.text_to_parse_key = 'definition line'
        self.set_parsing_rules(verbose=False)
        self.set_header_parsing_rules(verbose=False)

    def __next__(self):
        """Return definition line, sequence and quality scores"""
        lines = []
        for i in range(self.nlines):
            lines.append(self._safe_readline().replace('\n', ''))

        output = {
            'definition line':lines[0], 
            'ref_seq_aligned':f"{lines[1]}", 
            'read_seq_aligned': f"{lines[2]}",
        }   
        return output
    
    def read_header(self):
        """Read ALN file Header and return each section parsed in a dictionary"""
        
        header = {}
        if self.fp is not None:
            self.fp.close()
        self.fp = open(self.path, 'r')
        
        line = self._safe_readline().replace('\n', '')
        if not line.startswith('##ART_Illumina'): 
            raise ValueError(f"Header of this file does not start with ##ART_Illumina")
        line = self._safe_readline().replace('\n', '')
        if not line.startswith('@CM'): 
            raise ValueError(f"First header line should start with @CM")
        else: 
            header['command'] = line[3:].replace('\t', '').strip()

        refseqs = []
        while True:
            line = self._safe_readline().replace('\n', '')
            if line.startswith('##Header End'): break
            else:
                refseqs.append(line)
        header['reference sequences'] = refseqs
        
        return header
    
    def reset_iterator(self):
        """Reset the iterator to point to the first line in the file, by recreating a new file handle.
        
        `AlnFileReader` requires a specific `reset_iterator` method, in order to skip the header every time it is reset
        """
        if self.fp is not None:
            self.fp.close()
        self.fp = open(self.path, 'r')
        while True:
            line = self._safe_readline().replace('\n', '')
            if line.startswith('##Header End'): break
    
    def parse_file(
        self, 
        add_ref_seq_aligned:bool=False,   # Add the reference sequence aligned to the parsed dictionary when True
        add_read_seq_aligned:bool=False,  # Add the read sequence aligned to the parsed dictionary when True
    )-> dict[str]: 
        # Key/Values. Keys: 
        # `readid`,`seqid`,`seq_nbr`,`read_nbr`,`aln_start_pos`,`ref_seq_strand`
        # optionaly `ref_seq_aligned`,`read_seq_aligned`
        """Read ALN file, return a dict w/ alignment info for each read and optionaly aligned reference sequence & read"""
        self.reset_iterator()
        parsed = {}
        for d in self:
            dfn_line = d['definition line']
            ref_seq_aligned, read_seq_aligned = d['ref_seq_aligned'], d['read_seq_aligned']
            metadata = self.parse_text(dfn_line)
            if add_ref_seq_aligned: metadata['ref_seq_aligned'] = ref_seq_aligned         
            if add_read_seq_aligned: metadata['read_seq_aligned'] = read_seq_aligned
            parsed[metadata['readid']] = metadata 
        return parsed

    def parse_header_reference_sequences(
        self,
        pattern:str|None=None,     # regex pattern to apply to parse the reference sequence info
        keys:list[str]|None=None,  # list of keys: keys are both regex match group names and corresponding output dict keys 
        )->dict[str]:                  # parsed metadata in key/value format
        """Extract metadata from all header reference sequences"""
        if pattern is None and keys is None:
            pattern, keys = self.re_header_pattern, self.re_header_keys
        parsed = {}
        for seq_dfn_line in self.header['reference sequences']:
            metadata = self.parse_text(seq_dfn_line, pattern, keys)
            parsed[metadata['refseqid']] = metadata
            
        return parsed
            
        
    def set_header_parsing_rules(
        self,
        pattern: str|bool=None,   # regex pattern to apply to parse the text, search in parsing rules json if None
        keys: list[str]=None,     # list of keys/group for regex, search in parsing rules json if None
        verbose: bool=False       # when True, provides information on each rule
    )-> None:
        """Set the regex parsing rule for reference sequence in ALN header.
               
        Updates 3 class attributes: `re_header_rule_name`, `re_header_pattern`, `re_header_keys`
        
        TODO: refactor this and the method in Core: to use a single function for the common part and a parameter for               the text_to_parse 
        """
        
        P2JSON = Path('../default_parsing_rules.json')
        
        self.re_header_rule_name = None
        self.re_header_pattern = None
        self.re_header_keys = None
        
        # get the first reference sequence definition line in header
        text_to_parse = self.header['reference sequences'][0]
        divider_line = f"{'-'*80}"

        if pattern is not None and keys is not None:  # When specific pattern and keys are passed
            try:
                metadata_dict = self.parse_text(text_to_parse, pattern, keys)
                self.re_header_rule_name = 'Custom Rule'
                self.re_header_pattern = pattern
                self.re_header_keys = keys
                if verbose:
                    print(divider_line)
                    print(f"Custom rule was set for header in this instance.")
            except Exception as err: 
                raise ValueError(f"The pattern generates the following error:\n{err}")
                
        else:  # automatic rule selection among rules saved in json file
            # Load all existing rules from json file
            with open(P2JSON, 'r') as fp:
                parsing_rules = json.load(fp)
                
            # test all existing rules and keep the one with highest number of matches
            max_nbr_matches = 0
            for k, v in parsing_rules.items():
                re_header_pattern = v['pattern']
                re_header_keys = v['keys'].split(' ')
                try:
                    metadata_dict = self.parse_text(text_to_parse, re_header_pattern, re_header_keys)
                    nbr_matches = len(metadata_dict)
                    if verbose:
                        print(divider_line)
                        print(f"Rule <{k}> generated {nbr_matches:,d} matches")
                        print(divider_line)
                        print(re_header_pattern)
                        print(re_header_keys)

                    if len(metadata_dict) > max_nbr_matches:
                        self.re_header_pattern = re_header_pattern
                        self.re_header_keys = re_header_keys
                        self.re_header_rule_name = k    
                except Exception as err:
                    if verbose:
                        print(divider_line)
                        print(f"Rule <{k}> generated an error")
                        print(err)
                    else:
                        pass
            if self.re_header_rule_name is None:
                msg = """
        None of the saved parsing rules were able to extract metadata from the first line in this file.
        You must set a custom rule (pattern + keys) before parsing text, by using:
            `self.set_parsing_rules(custom_pattern, custom_list_of_keys)`
                """
                warnings.warn(msg, category=UserWarning)
            
            if verbose:
                print(divider_line)
                print(f"Selected rule with most matches: {self.re_header_rule_name}")

            # We used the iterator, now we need to reset it to make all lines available
            self.reset_iterator()
    
    @property
    def ref_sequences(self):
        refseq_metadata = {}
        for refseq in self.header['reference sequences']:
            
            meta = parse_art_read_aln_refseqs(refseq)
            refseq_metadata[meta['refseqid']] = meta
        
        return refseq_metadata

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 117
def create_infer_ds_from_fastq(
    p2fastq: str|Path,             # Path to the fastq file (aln file path is inferred)
    output_dir:str|Path|None=None, # Path to directory where ds file will be saved
    overwrite_ds:bool=False,       # If True, overwrite existing ds file. If False, error is raised if ds file exists
    nsamples:int|None=None         # Used to limit the number of reads to use for inference, use all if None
)-> (Path, np.ndarray):      # Path to the dataset file, Array with additional read information
    """Build a dataset file for inference only, from simreads fastq to text format ready for the CNN Virus model
    
    > Note: currently also return additional read information as an array. 
    >
    > TODO: consider to save as a file
    """
    fastq = FastqFileReader(p2fastq)
    aln = AlnFileReader(p2fastq.parent / f"{p2fastq.stem}.aln")
    
    if output_dir is None:
        p2dir = Path()
    else:
        validate_path(output_dir, path_type='dir', raise_error=True)
        p2outdir = output_dir if isinstance(output_dir, Path) else Path(output_dir)
    
    p2dataset = p2outdir / f"{p2fastq.stem}_ds"
    if p2dataset.is_file():
        if overwrite_ds: 
            p2dataset.unlink()
        else:
            raise ValueError(f"{p2dataset.name} already exists in {p2dataset.absolute()}")
    p2dataset.touch()
    
    read_ids = []
    read_refseqs = []
    read_start_pos = []
    read_strand = []
    
    with open(p2dataset, 'a') as fp:
        i = 1
        for fastq_chunk, aln_chunk in zip(fastq.it, aln.it):
            seq = fastq_chunk['sequence']
            
            aln_meta = parse_metadata_art_read_aln(aln_chunk['definition line'])
#             print(aln_meta.keys())
            read_ids.append(aln_meta['readid'])
            read_refseqs.append(aln_meta['refseqid'])
            read_start_pos.append(aln_meta['aln_start_pos'])
            read_strand.append(aln_meta['refseq_strand'])

            fp.write(f"{seq}\t{0}\t{0}\n")
#             print(f"{seq}\t{0}\t{0}\n")

            i += 1
            if nsamples:
                if i > nsamples: break
                    
    print(f"Dataset with {i-1:,d} reads")    
    return p2dataset, np.array(list(zip(read_ids, read_refseqs, read_start_pos, read_strand)))


# %% ../../nbs-dev/03_cnn_virus_data.ipynb 120
def strings_to_tensors(
    b: tf.Tensor        # batch of strings 
    ):
    """Function converting a batch of bp strings into three tensors: (x_seqs, (y_labels, y_pos))"""
    
    # Split the string in three : returns a ragged tensor which needs to be converted into a normal tensor using .to_tensor()
    t = tf.strings.split(b, '\t').to_tensor(default_value = '', shape=[None, 3])

    # Split each sequence string into a list of single base strings:
    # 'TCAAAATAATCA' -> ['T','C','A','A','A','A','T','A','A','T','C','A']
    seqs = tf.strings.bytes_split(t[:, 0]).to_tensor(shape=(None, 50))


    # BHE sequences
    # Each base letter (A, C, G, T, N) is replaced by a OHE vector
    #     "A" converted into [1,0,0,0,0]
    #     "C" converted into [0,1,0,0,0]
    #     "G" converted into [0,0,1,0,0]
    #     "T" converted into [0,0,0,1,0]
    #     "N" converted into [0,0,0,0,1]
    # 
    # Technical Notes:
    # a. The batch of sequence `seqs` has a shape (batch_size, 50) after splitting each byte. 
    #    Must flatten it first, then apply the transform on each base, then reshape to original shape
    # b. We need to map each letter to one vector/tensor. 
    #    1. Cast bytes seqs into integer sequence (uint8 to work byte by byte)
    #    2. For each base letter (A, C, G, T, N) create one tensor (batch_size, 50) (seqs_A, _C, _G, _T, _N)
    #    3. Value is 1 if it is the base in the sequence, otherwise 0
    #    4. Concatenate these 5 tensors into a tensor of shape (batch_size, 50, 5)
 
    seqs_uint8 = tf.io.decode_raw(seqs, out_type=tf.uint8)
    # note: tf.io.decode_raw adds one dimension at the end in the process
    #       [b'C', b'A', b'T'] will return [[67], [65], [84]] and not [67, 65, 84]
    #       this is actually what we want to contatenate the values for each base letter

    A, C, G, T, N = 65, 67, 71, 84, 78

    seqs_A = tf.cast(seqs_uint8 == A, tf.float32)
    seqs_C = tf.cast(seqs_uint8 == C, tf.float32)
    seqs_G = tf.cast(seqs_uint8 == G, tf.float32)
    seqs_T = tf.cast(seqs_uint8 == T, tf.float32)
    seqs_N = tf.cast(seqs_uint8 == N , tf.float32)

    x_seqs = tf.concat([seqs_A, seqs_C, seqs_G, seqs_T, seqs_N], axis=2)

    # OHE labels
    n_labels = 187
    y_labels = tf.strings.to_number(t[:, 1], out_type=tf.int32)
    y_labels = tf.gather(tf.eye(n_labels), y_labels)

    # OHE positions
    n_pos = 10
    y_pos = tf.strings.to_number(t[:, 2], out_type=tf.int32)
    y_pos= tf.gather(tf.eye(n_pos), y_pos)

    return (x_seqs, (y_labels, y_pos))
