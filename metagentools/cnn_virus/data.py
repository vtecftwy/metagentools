# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs-dev/03_cnn_virus_data.ipynb.

# %% auto 0
__all__ = ['FastaFileIterator', 'base_metadata_parser', 'parse_metadata_fasta_cov', 'FastaMetadataIterator', 'FastaFileReader',
           'FastqFileIterator', 'parse_metadata_art_reads', 'FastqFileReader', 'AlnFileIterator',
           'parse_metadata_art_read_aln', 'parse_art_read_aln_refseqs', 'AlnFileReader', 'create_infer_ds_from_fastq',
           'strings_to_tensors']

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 3
from ecutilities.core import validate_path
from functools import partial, partialmethod
from ..bio import q_score2prob_error
from ..core import TextFileBaseIterator
from pathlib import Path
from typing import Any, Optional

import json
import numpy as np
import re
import tensorflow as tf

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 26
class FastaFileIterator(TextFileBaseIterator):
    """Iterator going through a fasta file sequence by sequence and returning definition line and sequence as a dict"""
    def __init__(
        self,
        path:str|Path,   # path to the fasta file
    ):
        super().__init__(path, nlines=1)
    
    def __next__(self)-> dict[str, str]:   # `{'definition line': text in dfn line, 'sequence': full sequence as str}` 
        """Return one definition line and the corresponding sequence"""
        lines = []
        for i in range(2):
            lines.append(self._safe_readline())
        dfn_line = lines[0]
        sequence = lines[1].replace('\n', '')
        return {'definition line':dfn_line, 'sequence':f"{sequence}"}
    
    def print_first_chuncks(
        self, 
        nchunks:int=3,  # number of chunks to print out
    ):
        """Print the first `nchunks` chuncks of text from the file"""
        for i, seq_dict in enumerate(self.__iter__()):
            print(f"\nSequence {i+1}:")
            print(seq_dict['definition line'])
            print(f"{seq_dict['sequence'][:80]} ...")
            if i >= nchunks: break

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 33
def base_metadata_parser(
    txt:str,         # string to parse
    pattern:str,     # regex pattern to apply to parse the string
    keys:list[str],  # list of keys: keys are both the regex match group names and the corresponding output dict keys
)-> dict:            # parsed metadata in key/value format
    """Basic parser fn parsing metadata from string, using regex pattern and return a metadata dictionary"""
    matches = re.match(pattern, txt)
    metadata = {}
    if matches is not None:
        for g in sorted(keys):
            m = matches.group(g)
            metadata[g] = m.replace('\t', ' ').strip() if m is not None else None
        return metadata
    else:
        raise ValueError(f"No match on this line")

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 41
def parse_metadata_fasta_cov(
    txt:str,                       # definition line in covid sequence fasta file
    pattern:Optional[str]=None,    # regex pattern to apply to parse the definition line
    keys: Optional[list[str]]=None # list of keys: keys are both the regex match group names and the corresponding output dict keys
)-> dict:                          # parsed metadata in key/value format
    """Parse metadata from one sequence definition line and return a metadata dictionary
    
    By default, `pattern` and `keys` are set to match the format of the project cov sequences
    """
    if pattern is None:
        pattern = r"^>(?P<seqid>(?P<taxonomyid>\d+):(?P<source>ncbi):(?P<seqnb>\d*))[\s\t]*\[(?P<accession>[\w\d]*)\]([\s\t]*(?P=taxonomyid)[\s\t]*(?P=source)[\s\t]*(?P=seqnb)[\s\t]*\[(?P=accession)\][\s\t]*(?P=taxonomyid)[\s\t]*(?P<species>[\w\s\-\_\/]*))?"
    if keys is None: keys = 'seqid taxonomyid source accession seqnb species'.split(' ')
    return base_metadata_parser(txt, pattern, keys)

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 45
class FastaMetadataIterator(FastaFileIterator):
    """Parse all definition lines in a FASTA file for metadata"""
    def get_metadata(
        self,
        save_json:bool=False  # save metadata as json if True
    )-> dict: # key/value where key is SeqID and value is metadata `dict`
        """returns metadata as a dictionary and optionally save as json next to original fasta file:

        - keys are the `SeqID` for each sequence in the fasta file
        - values are `dict` with parsed metadata from the corresponding sequence definition line
        """       
        fasta_metadata = {}
        for o in self.__iter__():
            dfn_line = o['definition line']
            seq_metadata = parse_metadata_fasta_cov(dfn_line)
            fasta_metadata[seq_metadata['seqid']] = seq_metadata
        
        if save_json:
            p2json = self.path.parent / f"{self.path.stem}_metadata.json"
            with open(p2json, 'w') as fp:
                json.dump(fasta_metadata, fp, indent=4)
                print(f"Metadata for '{self.path.name}'> saved as <{p2json.name}> in  \n{p2json.parent.absolute()}\n")
            
        return fasta_metadata

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 50
class FastaFileReader:
    """Wrap a FASTA file and retrieve its contend in raw format and parsed format"""
    def __init__(
        self,
        path: str|Path,  # path to the Fasta file
    ):
        validate_path(path, raise_error=True)
        self.path = path
        self.it = None
        self.reset_iterator()
        
    def reset_iterator(self):
        """Reset the iterator to first file line"""
        self.it = FastaFileIterator(self.path)
        
    def parse_fasta(
        self,
        add_seq:bool=False,    # Add the full sequence to the parsed dictionary when True
    )-> dict[str]:              # Key/Values for keys: `seqid`, `seq_nbr`, `accession`, `species` and optionaly `sequence`
        """Read fasta file and return a dictionary with definition line metadata and optionally sequences"""
        self.reset_iterator()
        parsed = {}
        for d in self.it:
            dfn_line = d['definition line']
            seq = d['sequence']
            metadata = parse_metadata_fasta_cov(dfn_line)
            if add_seq: metadata['sequence'] = seq         
            parsed[metadata['seqid']] = metadata
        return parsed

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 65
class FastqFileIterator(TextFileBaseIterator):
    """Iterator going through a fastq file's sequences and return each section + prob error as a dict"""
    def __init__(
        self,
        path:str|Path,   # path to the fastq file
    )-> dict:           # key/value with keys: definition line; sequence; q score; prob error
        self.nlines = 4
        super().__init__(path, nlines=self.nlines)
    
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
    
#     def print_first_chuncks(
#         self, 
#         nchunks:int=3,  # number of chunks to print out
#     ):
#         """Print the first `nchunks` chuncks of text from the file"""
#         for i, seq_dict in enumerate(self.__iter__()):
#             print(f"\nSequence {i+1}:")
#             print(seq_dict['definition line'])
#             print(f"{seq_dict['sequence'][:80]} ...")
#             if i >= nchunks: break

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 72
def parse_metadata_art_reads(
    txt:str,                   # definition line in ART read definition line
    pattern:str|None=None,     # regex pattern to apply to parse the definition line
    keys:list[str]|None=None,  # list of keys: keys are both regex match group names and corresponding output dict keys 
)->dict[str]:                  # parsed metadata in key/value format
    """Parse metadata from one read definition line and return a metadata dictionary

    By default, pattern and keys are set to match the output format of ART Illumina simulated reads"""
    if pattern is None:
        pattern = r"^@(?P<readid>(?P<reftaxonomyid>\d*):(?P<refsource>\w*):(?P<refseqnb>\d*)-(?P<readnb>\d*))$"
    if keys is None: keys = 'readid reftaxonomyid refsource refseqnb readnb'.split(' ')
    return base_metadata_parser(txt, pattern, keys)

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 75
class FastqFileReader:
    """Wrap a FASTQ file and retrieve its content in raw format and parsed format"""
    def __init__(
        self,
        path: str|Path,  # path to the Fastq file
    ):
        validate_path(path, raise_error=True)
        self.path = path
        self.it = None
        self.reset_iterator()
        
    def reset_iterator(self):
        """Reset the iterator to first file line"""
        self.it = FastqFileIterator(self.path)
        
    def parse_fastq(
        self, 
        add_readseq:bool=False,        # Add the read sequence to the parsed dictionary when True
        add_qscores:bool=False,    # Add the read ASCII Q Scores to the parsed dictionary when True
        add_probs_error:bool=False  # Add the read probability of error to the parsed dictionary when True
    )-> dict[str]: # Key/Values. Keys: `seqid`,`seq_nbr`,`accession`,`species`; optionaly 'sequence','q scores','prob error'
        """Read fasta file and return a dictionary with definition line metadata and optionally sequences, Q scores and prop error"""
        self.reset_iterator()
        parsed = {}
        for d in self.it:
            dfn_line = d['definition line']
#             print(dfn_line)
            seq, q_scores, prob_e = d['sequence'], d['read_qscores'], d['probs error']
            metadata = parse_metadata_art_reads(dfn_line)
            if add_readseq: metadata['readseq'] = seq         
            if add_qscores: metadata['read_qscores'] = q_scores
            if add_probs_error: metadata['probs error'] = prob_e
            parsed[metadata['readid']] = metadata 
        return parsed

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 81
class AlnFileIterator(TextFileBaseIterator):
    """Iterator going through aln file"""
    def __init__(
        self,
        path:str|Path,   # path to the aln file
    )-> dict:            # key/value with keys: 
        self.nlines = 1
        super().__init__(path, nlines=self.nlines)
        self.header = self.read_header()
        self.nlines = 3
    
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
        """Read ALN file Header and return a each section parsed in a dictionary"""
        
        header = {}
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
            
    
#     def print_first_chuncks(
#         self, 
#         nchunks:int=3,  # number of chunks to print out
#     ):
#         """Print the first `nchunks` chuncks of text from the file"""
#         for i, seq_dict in enumerate(self.__iter__()):
#             print(f"\nSequence {i+1}:")
#             print(seq_dict['definition line'])
#             print(f"{seq_dict['sequence'][:80]} ...")
#             if i >= nchunks: break

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 89
def parse_metadata_art_read_aln(
    txt:str,                   # definition line in ALN read definition line
    pattern:str|None=None,     # regex pattern to apply to parse the definition line
    keys:list[str]|None=None,  # list of keys: keys are both regex match group names and corresponding output dict keys 
)->dict[str]:                  # parsed metadata in key/value format
    """Parse metadata from one read aligmnent definition line and return a metadata dictionary

    By default, pattern and keys are set to match the output format of ART Illumina simulated reads"""
    if pattern is None:
        pattern = r"^>(?P<refseqid>(?P<reftaxonomyid>\d*):(?P<refsource>\w*):(?P<refseqnb>\d*))(\s|\t)*(?P<readid>(?P=reftaxonomyid):(?P=refsource):(?P=refseqnb)-(?P<readnb>\d*(\/\d(-\d)?)?))(\s|\t)(?P<aln_start_pos>\d*)(\s|\t)(?P<refseq_strand>(-|\+))$"
    if keys is None: keys = 'refseqid reftaxonomyid refsource refseqnb readid readnb aln_start_pos refseq_strand'.split(' ')
    return base_metadata_parser(txt, pattern, keys)

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 92
def parse_art_read_aln_refseqs(
    txt:str,                   # reference sequence info in the ALN header
    pattern:str|None=None,     # regex pattern to apply to parse the reference sequence info
    keys:list[str]|None=None,  # list of keys: keys are both regex match group names and corresponding output dict keys 
)->dict[str]:                  # parsed metadata in key/value format
    """Parse metadata from one reference sequence from the ALN header and return a metadata dictionary

    By default, pattern and keys are set to match the output format of ART Illumina simulated reads"""
    if pattern is None:
        pattern = r"^@SQ[\t\s]*(?P<refseqid>(?P<reftaxonomyid>\d*):(?P<refsource>\w*):(?P<refseqnb>\d*))[\t\s]*\[(?P<refseq_accession>[\d\w]*)\][\t\s]*(?P=reftaxonomyid)[\s\t]*(?P=refsource)[\s\t]*(?P=refseqnb)[\s\t]*\[(?P=refseq_accession)\][\s\t]*(?P=reftaxonomyid)[\s\t]*(?P<species>\w[\w\d\/\s-]*\s)[\s\t]*(?P<refseq_length>\d*)$"
    if keys is None: keys = 'refseqid reftaxonomyid refsource refseqnb refseq_accession species refseq_length'.split(' ')
        
    return base_metadata_parser(txt, pattern, keys)

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 95
class AlnFileReader:
    """Wrap an ALN alignment file and retrieve its content in raw format and parsed format"""
    def __init__(
        self,
        path: str|Path,  # path to the ALN file
    ):
        validate_path(path, raise_error=True)
        self.path = path
        self.it = None
        self.reset_iterator()
        
    def reset_iterator(self):
        """Reset the iterator to first file line"""
        self.it = AlnFileIterator(self.path)
        
    def parse_aln(
        self, 
        add_ref_seq_aligned:bool=False,   # Add the reference sequence aligned to the parsed dictionary when True
        add_read_seq_aligned:bool=False,  # Add the read sequence aligned to the parsed dictionary when True
    )-> dict[str]: # Key/Values. Keys: `readid`,`seqid`,`seq_nbr`,`read_nbr`,`aln_start_pos`,`ref_seq_strand`; optionaly 'ref_seq_aligned','read_seq_aligned'
        """Read ALN file and return a dictionary with alignment info for each read and optionaly the aligned reference sequence and read"""
        self.reset_iterator()
        parsed = {}
        for d in self.it:
            dfn_line = d['definition line']
            ref_seq_aligned, read_seq_aligned = d['ref_seq_aligned'], d['read_seq_aligned']
            metadata = parse_metadata_art_read_aln(dfn_line)
            if add_ref_seq_aligned: metadata['ref_seq_aligned'] = ref_seq_aligned         
            if add_read_seq_aligned: metadata['read_seq_aligned'] = read_seq_aligned
            parsed[metadata['readid']] = metadata 
        return parsed

    @property
    def header(self):
        return self.it.header
    
    @property
    def ref_sequences(self):
        refseq_metadata = {}
        for refseq in self.it.header['reference sequences']:
            meta = parse_art_read_aln_refseqs(refseq)
            refseq_metadata[meta['refseqid']] = meta
        
        return refseq_metadata

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 106
def create_infer_ds_from_fastq(
    p2fastq: str|Path,       # Path to the fastq file (aln file path is inferred)
    overwrite_ds:bool=False, # When True, existing ds file is overwritten, When False, an error is raised if ds exists
    nsamples:int|None=None   # Used to limit the number of reads to use for inference, use all if None
)-> (Path, np.ndarray):      # Path to the dataset file, Array with additional read information
    """Build a dataset file for inference only, from simreads fastq to text format ready for the CNN Virus model
    
    > Note: currently also return additional read information as an array. 
    >
    > TODO: consider to save as a file
    """
    fastq = FastqFileReader(p2fastq)
    aln = AlnFileReader(p2fastq.parent / f"{p2fastq.stem}.aln")
    
    p2dataset = Path(f"{p2fastq.stem}_ds")
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
        for fastq_chunck, aln_chunck in zip(fastq.it, aln.it):
            seq = fastq_chunck['sequence']
            
            aln_meta = parse_metadata_art_read_aln(aln_chunck['definition line'])
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

# %% ../../nbs-dev/03_cnn_virus_data.ipynb 109
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
