# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs-dev/02_art.ipynb.

# %% auto 0
__all__ = ['ArtIllumina']

# %% ../nbs-dev/02_art.ipynb 2
# Imports all dependencies
import os
import subprocess
import shlex

from fastcore.basics import patch_to
from fastcore.utils import run, join_path_file
from pathlib import Path
from typing import Tuple, List, Optional

# %% ../nbs-dev/02_art.ipynb 6
# Private Utility functions to export ==============================================

def _run(args: List[str], shell: bool=False):
    """Wrapper subprocess.run and prints the output"""
    p = subprocess.run(args=args, stdout=subprocess.PIPE, shell=shell)
    print('return code: ',p.returncode, '\n')
    print(str(p.stdout, 'utf-8'))

def _validate_path(p:str|Path) -> Path:
    """checks that path is a string or a Path, and returns a Path"""
    if isinstance(p, str): 
        p = Path(p)
    elif not isinstance(p, Path): 
        raise TypeError(f"a path must be a string or a Path, not a {type(p)}")
    return p

# %% ../nbs-dev/02_art.ipynb 7
class ArtIllumina:
    """Class to handle all aspects of simulating sequencing with art_illumina"""

    QUALITY_PROFILES = {
        'GA1': 'GenomeAnalyzer I (36bp,44bp)', 'GA2': 'GenomeAnalyzer II (50bp, 75bp)',
        'HS10': 'HiSeq 1000 (100bp)', 'HS20': 'HiSeq 2000 (100bp)',
        'HS25': 'HiSeq 2500 (125bp, 150bp)', 'HSXn': 'HiSeqX PCR free (150bp)', 'HSXt': 'HiSeqX TruSeq (150bp)',
        'MinS': 'MiniSeq TruSeq (50bp)', 'MSv1': 'MiSeq v1 (250bp)', 'MSv3': 'MiSeq v3 (250bp)',
        'NS50': 'NextSeq500 v2 (75bp)'
        }

    def __init__(
        self, 
        path2app: str|Path,           # path to the art_illumina application on the system
        input_dir: str|Path,          # path to dir where input files are
        output_dir: str|Path=None     # path to dir where to save output files, if different from input_dir
        ):
        """Initialize the art_illumina instance"""

        # Validate and save paths
        path2app = _validate_path(path2app)        
        if path2app.is_file():
            self.app = path2app
        else:
            raise ValueError(f"{path2app.name} is not a file, please check the path to the application")

        input_dir = _validate_path(input_dir)
        if input_dir.is_dir():
            self.input_dir = input_dir
        else:
            raise ValueError(f"{input_dir.name} is not a directory, please check the path")

        if output_dir is None: 
            self.output_dir = input_dir
        else:
            output_dir = _validate_path(output_dir)
            if output_dir.is_dir():
                self.output_dir = output_dir
            else:
                raise ValueError(f"{input_dir.name} is not a directory, please check the path")

        print(f"Ready to operate with art: {self.app.absolute()}")
        print(f"Input files from : {self.input_dir.absolute()}")
        print(f"Output files to :  {self.output_dir.absolute()}")

    def sim_reads(
        self,
        input_file: str,          # name of the fasta file to use as input
        output_seed: str,         # seed to use for the output files
        sim_type: str='single',   # type of read simmulation: 'single' or 'paired'
        read_length: int=150,     # length of the read in bp
        fold: int=10,             # fold
        mean_read: int=None,      # mean length of the read for paired reads
        std_read: int=None,       # std of the read length, for paired reads
        ss: str='HS25',           # quality profile to use for simulation,
        overwrite: bool=False     # overwrite existing output files if true, raise error if false 
        ):
        """Simulates reads with art_illumina. Output files saved in a separate directory"""

        # validate input file and save in instance
        path2inputfile = self.input_dir / input_file
        if path2inputfile.is_file(): 
            self.last_input_file = path2inputfile
        else:
            raise ValueError(f"{input_file} is not a file in {self.input_dir}")

        # validate output seed and save in instance
        if not overwrite and len(list(self.output_dir.glob(f"{output_seed}*"))) > 0: 
            raise ValueError(f"Existing output directory starting with {output_seed}")
        else:
            self.last_output_seed = output_seed
            self.last_read_output_dir = self.output_dir/self.last_output_seed
            os.makedirs(self.last_read_output_dir, exist_ok=True)

        # validate quality profile
        if ss not in list(self.QUALITY_PROFILES.keys()): 
            raise ValueError(f"{ss} is not a built-in profile.\nPick one of these: {self.QUALITY_PROFILES}")

        # build art_illumina command
        if sim_type == 'single':
            params = f"-ss {ss} -l {read_length} -f {fold}"
        elif sim_type == 'paired':
            if mean_read is None or std_read is None:
                raise ValueError(f"mean_read and std_read are required for a paired reads simulation")
            else:
                params = f"-ss {ss} -p -l {read_length} -f {fold} -m {mean_read} -s {std_read}"
        else:
            raise RuntimeError(f"{sim_type} in not a type or is not implemented yet")

        p2in = self.last_input_file.absolute()
        p2out = (self.output_dir / self.last_output_seed / self.last_output_seed).absolute()

        cmd = f"{self.app.absolute()} -i {p2in} {params} -o {p2out}"

        _run(args=shlex.split(cmd))

    def get_last_output_files(self):
        """Returns the path to all output files from last simulation"""
        return [f for f in self.last_read_output_dir.iterdir()]

    def list_last_output_files(self):
        """Prints a list of the last simulation's output files"""
        for f in self.get_last_output_files():
            print(f.name)

    def list_all_input_files(self):
        for f in sorted(list(self.input_dir.iterdir())):
            print(f.name)

    def get_all_output_files(self):
        """Return a dictionary with k as output file subdirectory and v as list of output files"""
        all_output_files = {}
        for d in sorted([p for p in self.output_dir.iterdir() if p.is_dir()]):
            files = []
            for f in d.iterdir():
                files.append(f)
            all_output_files[d.name] = files

        return all_output_files

    def list_all_output_files(self):
        all_files = self.get_all_output_files()
        for k, v in all_files.items():
            print(k)
            print('\n'.join([f"- {p.name}" for p in v]))
        
    def print_last_output_file_excerpts(
        self, 
        suffix: str='fq',        # suffix of the files to explore: 'fq', 'aln', 'sam' 
        nlines: int=12          # number of lines to print for each file
        ):
        """Print the first lines of all the latest file with given suffix"""

        for p in [p for p in self.get_last_output_files() if p.suffix == f".{suffix}"]:
            print(f"{'='*120}")
            print(f"File Name: {p.name}.")
            print(f"{'-'*80}")
            with open(p, 'r') as f:
                n, lines = 0, []
                while True:
                    n += 1
                    line = f.readline()
                    if line == '': break
                    elif n > nlines: break
                    else:
                        lines.append(line)

            print(''.join(lines))