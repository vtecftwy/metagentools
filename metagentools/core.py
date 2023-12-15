# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs-dev/00_core.ipynb.

# %% auto 0
__all__ = ['CODE_ROOT', 'PACKAGE_ROOT', 'TextFileBaseReader', 'JsonFileReader', 'ProjectFileSystem', 'TextFileBaseIterator']

# %% ../nbs-dev/00_core.ipynb 4
import configparser
import json
import os
import re
import sys
import warnings
from ecutilities.core import is_type, safe_path
from pathlib import Path
from pprint import pprint
from typing import Any, Optional

try: from google.colab import drive
except: pass

# %% ../nbs-dev/00_core.ipynb 5
# Retrieve the package root
from . import __file__
CODE_ROOT = Path(__file__).parents[0]
PACKAGE_ROOT = Path(__file__).parents[1]

# %% ../nbs-dev/00_core.ipynb 7
class TextFileBaseReader:
    """Iterator going through a text file by chunks of `nlines` lines. Iterator can be reset to file start.
    
    The class is mainly intented to be extended, in particular for handling sequence files or other type of data files
    """


    def __init__(
        self,
        path: str|Path,  # path to the file
        nlines: int=3,   # number of lines on one chunk
    ):
        self.path = safe_path(path)
        self.nlines = nlines
        self.fp = None
        self.reset_iterator()
        
        # Attributes related to metadata parsing
        # Currently assumes the iterator generates a dictionary with key/values
        # TODO: extend to iterator output as simple string.
        self.text_to_parse_key = None
        self.parsing_rules_json = Path(f"{PACKAGE_ROOT}/default_parsing_rules.json")
        self.re_rule_name = None
        self.re_pattern = None       # regex pattern to use to parse text
        self.re_keys = None          # keys (re group names) to parse text

    def reset_iterator(self):
        """Reset the iterator to point to the first line in the file, by recreating a new file handle."""
        if self.fp is not None:
            self.fp.close()
        self.fp = open(self.path, 'r')
        
    def __iter__(self):
        return self

    def _safe_readline(self):
        """Read a new line and handle end of file tasks."""
        line = self.fp.readline()
        if line == '':
            self.fp.close()
            raise StopIteration()
        return line

    def __next__(self):
        """Return one chunk at the time"""
        lines = []
        for i in range(self.nlines):
            lines.append(self._safe_readline())
        return ''.join(lines)
    
    def print_first_chunks(
        self, 
        nchunks:int=3,  # number of chunks to print
    ):
        """Print the first `nchunk` chunks of text from the file"""
        self.reset_iterator()
        for i, chunk in enumerate(self.__iter__()):
            if i > nchunks-1: break
            print(f"{self.nlines}-line chunk {i+1}")
            print(chunk)
        self.reset_iterator()
            
    def _parse_text_fn(
        self,
        txt:str,         # text to parse
        pattern:str,     # regex pattern to apply to parse the text
        keys:list[str],  # list of keys: keys are both the regex match group names and the corresponding output dict keys
    )-> dict:        # parsed metadata in key/value format
        """Basic parser function parsing metadata from string, using regex pattern. Return a metadata dictionary"""
        
        matches = re.match(pattern, txt)
        metadata = {}
        if matches is not None:
            for g in sorted(keys):
                m = matches.group(g)
                metadata[g] = m.replace('\t', ' ').strip() if m is not None else None
            return metadata
        else:
            raise ValueError(f"No match on this line")

    def parse_text(
        self,
        txt:str,              # text to parse
        pattern:str=None,     # If None, uses standard regex pattern to extract metadata, otherwise, uses passed regex
        keys:list[str]=None,  # If None, uses standard regex list of keys, otherwise, uses passed list of keys (str)
    )-> dict:                 # parsed metadata in key/value format
        """Parse text using regex pattern and key. Return a metadata dictionary
        
        The passed text is parsed using the regex pattern. The method return a dictionary in the format:
            {
                'key_1': 'metadata 1',
                'key_2': 'metadata 2',
                ...
            }
        
        """
        if pattern is None and keys is None:
            if self.re_pattern is not None and self.re_keys is not None:
                return self._parse_text_fn(txt, self.re_pattern, self.re_keys)
            else:
                raise ValueError('attribute re_pattern and re_keys are still None')
        elif pattern is None or keys is None:
            raise ValueError('pattern and keys must be either both None or both have a value')
        else:
            return self._parse_text_fn(txt, pattern, keys)
        
        
    def set_parsing_rules(
        self,
        pattern: str|bool=None,   # regex pattern to apply to parse the text, search in parsing rules json if None
        keys: list[str]=None,     # list of keys/group for regex, search in parsing rules json if None
        verbose: bool=False       # when True, provides information on each rule
    )-> None:
        """Set the standard regex parsing rule for the file.
        
        Rules can be set:
        
        1. manually by passing specific custom values for `pattern` and `keys`
        2. automatically, by testing all parsing rules saved in `parsing_rule.json` 
        
        Automatic selection of parsing rules works by testing each rule saved in `parsing_rule.json` on the first 
        definition line of the fasta file, and selecting the one rule that generates the most metadata matches.
        
        Rules consists of two parameters:
        
        - The regex pattern including one `group` for each metadata item, e.g `(?P<group_name>regex_code)`
        - The list of keys, i.e. the list with the name of each regex groups, used as key in the metadata dictionary
        
        This method updates the three following class attributes: `re_rule_name`, `re_pattern`, `re_keys`
      
        """
        # get the first definition line in the file to test the pattern
        # in base class, text_to_parse_key is not defined and automatic rule selection cannot be used
        # this must be handled in children classes
        if self.text_to_parse_key is None:
            msg = """
            `text_to_parse_key` is not defined in this class. 
            It is not possible to set a parsing rule.
            """
            warnings.warn(msg, category=UserWarning)
            return

        self.reset_iterator()
        first_output = next(self)
        text_to_parse = first_output[self.text_to_parse_key]
        divider_line = f"{'-'*80}"

        if pattern is not None and keys is not None:
            try:
                metadata_dict = self.parse_text(text_to_parse, pattern, keys)
                self.re_rule_name = 'Custom Rule'
                self.re_pattern = pattern
                self.re_keys = keys
                if verbose:
                    print(divider_line)
                    print(f"Custom rule was set for this instance.")
            except Exception as err: 
                raise ValueError(f"The pattern generates the following error:\n{err}")
                
        else:
            # Load all existing rules from json file
            with open(self.parsing_rules_json, 'r') as fp:
                parsing_rules = json.load(fp)
                
            # test all existing rules and keep the one with highest number of matches
            max_nbr_matches = 0
            for k, v in parsing_rules.items():
                re_pattern = v['pattern']
                re_keys = v['keys'].split(' ')
                try:
                    metadata_dict = self.parse_text(text_to_parse, re_pattern, re_keys)
                    nbr_matches = len(metadata_dict)
                    if verbose:
                        print(divider_line)
                        print(f"Rule <{k}> generated {nbr_matches:,d} matches")
                        print(divider_line)
                        print(re_pattern)
                        print(re_keys)

                    if len(metadata_dict) > max_nbr_matches:
                        self.re_pattern = re_pattern
                        self.re_keys = re_keys
                        self.re_rule_name = k    
                except Exception as err:
                    if verbose:
                        print(divider_line)
                        print(f"Rule <{k}> generated an error")
                        print(err)
                    else:
                        pass
            if self.re_rule_name is None:
                msg = """
        None of the saved parsing rules were able to extract metadata from the first line in this file.
        You must set a custom rule (pattern + keys) before parsing text, by using:
            `self.set_parsing_rules(custom_pattern, custom_list_of_keys)`
                """
                warnings.warn(msg, category=UserWarning)
            
            if verbose:
                print(divider_line)
                print(f"Selected rule with most matches: {self.re_rule_name}")

            # We used the iterator, now we need to reset it to make all lines available
            self.reset_iterator()


# %% ../nbs-dev/00_core.ipynb 28
class JsonFileReader:
    def __init__(self, path:str|Path # path to the json file
                ):
        self.path = safe_path(path)
        with open(path, 'r') as fp:
            self.d = json.load(fp)
    
    def add_item(self, 
                 key:str,  # key for the new item
                 item:dict # new item to add to the json as a dict
                ):
        self.d[key] = item
        return self.d

    def save_to_file(self, path=None):
        if path is None: 
            path = self.path
        else:
            path = safe_path(path)

        with open(path, 'w') as fp:
            json.dump(self.d, fp, indent=4)

# %% ../nbs-dev/00_core.ipynb 34
class ProjectFileSystem:
    """Class to set paths to key directories, according to whether the code is running locally or in the cloud."""

    _instance = None
    _config_dir = '.metagentools'
    _config_fname = 'metagentools.cfg'
    _shared_project_dir = 'Metagenomics'
    
    def __new__(cls, *args, **kwargs):
        # Create instance if it does not exist yet
        if cls._instance is None:
            cls.home = Path.home().resolve()
            cls.p2config = cls.home / cls._config_dir / cls._config_fname
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self, 
        mount_gdrive:bool=True  # True to mount Google Drive if running on Colab
        ):
            self.is_colab = 'google.colab' in sys.modules       
            if self.is_colab and mount_gdrive:
                drive.mount('/content/gdrive')
                self.gdrive = Path('/content/gdrive/MyDrive')

            self.is_kaggle = 'kaggle_web_client' in sys.modules
            if self.is_kaggle:
                raise NotImplemented(f"ProjectFileSystem is not implemented for Kaggle yet")

            if not self.is_colab and not self.is_kaggle and not self.is_local:
                msg = """
                      Code does not seem to run on the cloud but computer is not registered as local
                      If you are running on a local computer, you must register it as local by running
                        `ProjectFileSystem().register_as_local()`
                      before you can use the ProjectFileSystem class.
                      """
                warnings.warn(msg, UserWarning)

    def __call__(self): return self.is_local

    def info(self):
        print(f"Running {self.os} on {self.running_on}")
        print(f"Device's home directory: {self.home}")
        print(f"Project file structure:")
        print(f" - Root ........ {self.project_root} \n - Data Dir .... {self.data} \n - Notebooks ... {self.nbs}")

    
    def read_config(self):
        """Read config from the configuration file if it exists and return an empty config if does not"""
        cfg = configparser.ConfigParser()
        if self.p2config.is_file(): 
            cfg.read(self.p2config)
        else:
            cfg.add_section('Infra')
        return cfg

    def register_as_local(self):
        """Update the configuration file to register the machine as local machine"""
        cfg = self.read_config()
        os.makedirs(self.home/self._config_dir, exist_ok=True)
        cfg['Infra']['registered_as_local'] = 'True'
        with open(self.p2config, 'w') as fp:
            cfg.write(fp)
        return cfg

    @property
    def os(self): return sys.platform

    @property
    def project_root(self):
        if self.is_local:
            return PACKAGE_ROOT
        elif self.is_colab:
            return self.gdrive / self._shared_project_dir
        elif self.is_kaggle:
            raise NotImplemented(f"ProjectFileSystem is not implemented for Kaggle yet")
        else:
            raise ValueError('Not running locally, on Colab or on Kaggle')


    @property
    def data(self): return self.project_root / 'data'

    @property
    def nbs(self): return self.project_root / 'nbs'        

    @property
    def p2config(self): return self.home / self._config_dir / self._config_fname
        
    @property
    def is_local(self):
        """Return `True` if the current machine was registered as a local machine"""
        cfg = self.read_config()
        return cfg['Infra'].getboolean('registered_as_local', False)

    @property
    def running_on(self):
        """Return the device on which this is run: local, colab, kaggle, ..."""
        if self.is_local: device = 'local computer'
        elif self.is_colab: device = 'colab'
        elif self.is_kaggle: device = 'kaggle'
        else: device = 'unknown cloud server'
        return device
    

# %% ../nbs-dev/00_core.ipynb 49
class TextFileBaseIterator:
    """`TextFileBaseIterator` is a deprecated class, to be replaced by `TextFileBaseReader`"""
    def __init__(self, *args, **kwargs):
        msg = """`TextFileBaseIterator` is deprecated. Use `TextFileBaseReader` instead, with same capabilities and more."""
        raise DeprecationWarning(msg)
