# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs-dev/03_cnn_virus_utils.ipynb.

# %% auto 0
__all__ = ['setup_nb']

# %% ../../nbs-dev/03_cnn_virus_utils.ipynb 2
# import dependencies
from fastcore.utils import run
from pathlib import Path

# %% ../../nbs-dev/03_cnn_virus_utils.ipynb 5
def setup_nb(_dev=False) -> tuple:      # colab, path to data root, path to data
    """Sets up the colab or the local environment and paths"""
    try:
        from google.colab import drive
        ON_COLAB = True
        print('Running on colab')
        print('Installing project code')
        cmd = "pip install -U git+https://github.com/vtecftwy/metagentools.git@main"
        run(cmd)
        # Assumes shared gdrive dir accessible through shortcut `Metagenomics` under the root of gdrive.     
        drive.mount('/content/gdrive')
        p2dataroot = Path('/content/gdrive/MyDrive/Metagenonics')
        p2data =  p2dataroot / 'CNN_Virus_data'

    except ModuleNotFoundError:
        ON_COLAB = False
        print('Running locally')
        try:
            import metagentools
        except ModuleNotFoundError:
            raise ModuleNotFoundError('Cannot find package metagentools. Make sure you pip -e install it in your environment')
        if _dev:
            p2dataroot = Path('data_dev')
            p2data = Path('data_dev')
        else:
            p2dataroot = Path('../data').resolve()
            p2data =  p2dataroot / 'CNN_Virus_data'

    if not p2dataroot.is_dir(): raise ValueError(f"{p2dataroot} is not a directory")
    if not p2data.is_dir(): raise ValueError(f"{p2data} is not a directory")
    return ON_COLAB, p2dataroot, p2data

