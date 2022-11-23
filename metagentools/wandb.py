# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs-dev/01_wandb.ipynb.

# %% auto 0
__all__ = ['login_nb', 'WandbRun']

# %% ../nbs-dev/01_wandb.ipynb 2
# Imports all dependencies
import numpy as np
import os
import tensorflow as tf
import wandb

from pathlib import Path

# %% ../nbs-dev/01_wandb.ipynb 9
def login_nb(
    nb_file: str|Path=None   # name of the notebook (str) or path to the notebook (Path)
    ):
    """Logs in to WandB from the current notebook. Registers current notebooks as the source of code"""

    # Validate nb_file
    if nb_file is None:
        raise TypeError('login requires the file name of the current nb to allow code tracking')   
    if isinstance(nb_file, str):
        if nb_file[-6:] != '.ipynb': nb_file = f"{nb_file}.ipynb"
        nb_file = Path.cwd()/nb_file
    elif not isinstance(nb_file, Path):
        raise TypeError('nb_file must me a `str` or a `Path`')
    
    if not nb_file.is_file():
        raise ValueError(f"{nb_file.name} is not a file, please correct the file name")

    # Registers notebook as WandB code
    os.environ['WANDB_NOTEBOOK_NAME'] = str(nb_file.absolute())
    print(f"Logging in from notebook: {os.environ['WANDB_NOTEBOOK_NAME']}")

    wandb.login(relogin=False)    

# %% ../nbs-dev/01_wandb.ipynb 19
class WandbRun():
    """Manages a run with WandB and all registered actions performed while the run is active. Close run with .finish()"""
    
    def __init__(
        self,
        entity: str='', # the user or organization under which the run will be logged. Default: `metagenomics_sh` 
        project: str='', # the name of the WandB project under which the run will be logged 
        run_name: str='', # unique name for the run,
        job_type: str='', # e.g.: `load_datasets`, `train_exp`, ... 
        notes: str='', # (optional) any text description or additional information to store with the run 
        testing: bool=False # (optional) If True, will not create a run on WandB. Use for local testing
        ) -> wandb.sdk.wandb_run.Run:
        """Validates metadata inputs and initialize the wandb run, unless testing is set to True"""
        
        # Validate inputs
        for k,v in [key_val for key_val in locals().items() if key_val[0] not in ['self', 'notes', 'testing']]:
            if v == '': raise ValueError(f"{k} may not be an empty string. Please provide a value")

        for k,v in [key_val for key_val in locals().items() if key_val[0] not in ['self', 'testing']]:
            if not isinstance(v, str): raise TypeError(f"{k} must be a string, not a {type(v)}")

        self.entity = entity
        self.project = project
        self.run_name = run_name
        self.job_type = job_type
        self.notes = notes
        
        if not testing:
            self.run = wandb.init(
                entity=entity, 
                project=project, 
                name=run_name, 
                job_type=job_type, 
                notes=notes, 
                save_code=True,
                dir= Path('../wandb-logs').resolve()
            )


    def finish(self):
        """End the run"""
        self.run.finish()
