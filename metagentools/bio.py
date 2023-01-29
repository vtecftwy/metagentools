# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs-dev/03_bio.ipynb.

# %% auto 0
__all__ = ['p_error_from_q_score_char', 'parse_metadata_from_definition_line', 'parse_metadata_from_fasta']

# %% ../nbs-dev/03_bio.ipynb 22
def p_error_from_q_score_char(
    char:str,             # ASCII character retrieved from Q Score or Phred value in FASTQ
    ASCII_base:int=33     # ASCII base. Mostly 33, can be 64 in old FASTQ files
):
    """Return the probability of error for a given Q score encoded as ASCII character"""
    ASCII_code = ord(char)
    Q = ASCII_code - ASCII_base
    p_error = 10**(-Q/10)
    return p_error

# %% ../nbs-dev/03_bio.ipynb 35
def parse_metadata_from_definition_line(
    line:str,                   # Definition line in covid sequence fasta file
    pattern:str|None = None,    # Optional regex pattern for definition lines when format is not our standard
)-> dict:                       # dictionary with key/value metadata
    """Parse metadata from one sequence fasta definition line and return a metadata dictionary"""
    if pattern is None:
        pattern = r"^>(?P<seqid>\d+):(?P<source>ncbi):(?P<seq_nbr>\d*)(\s*|\t*)\[(?P<accession>\w*\d*)\](\s*\n|((\s*|\t)(?P=seqid))(\s*|\t)(?P=source)(\s*|\t)\d*(\s*|\t)\[(?P=accession)\](\s*|\t)(?P=seqid)(\s*|\t)(?P<species>.*)(\s*|\t)scientific name\s*\n)"
    matches = re.match(pattern, line)
    metadata = {}
    if matches is not None:
        for g in 'seqid accession seq_nbr species'.split(' '):
            m = matches.group(g)
            metadata[g] = m.replace('\t', ' ').strip() if m is not None else None
        return metadata
    else:
        raise ValueError(f"No match on this line")

# %% ../nbs-dev/03_bio.ipynb 37
def parse_metadata_from_fasta(
    path: str|Path,                 # path to the fasta sequence file
    return_metadata: bool = False   # return the metadata dictionary if True
)-> dict:                           # dictionary whose keys are the sequence SeqID and values are metadata dicts
    """Parse metadata for each sequence in sequence file and save a json file"""
    # validate path
    if isinstance(path, str): path = Path(path)
    if not path.is_file(): raise ValueError(f"Cannot find a file at {path.absolute}. Check the path")
    
    with open(path, 'r') as fp:
        dfn_lines = []
        sequences = []
        while True:
            line = fp.readline()
            if line == '': break
            if line[0] == '>':
                dfn_lines.append(line)
            if line[0] in 'ACGT':
                sequences.append(line)
    seqs_metadata = {}
    for line in dfn_lines:
        metadata = parse_metadata_from_definition_line(line)
        seqs_metadata[metadata['seqid']] = metadata

    p2json = path.parent / f"{path.stem}_metadata.json"
    with open(p2json, 'w') as fp:
        json.dump(seqs_metadata, fp, indent=4)
    print(f"Metadata for '{path.name}'> saved as \n{p2json.absolute()}")

    
    if return_metadata: return seqs_metadata
