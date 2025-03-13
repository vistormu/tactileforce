import os
import shutil
from catasta.utils import split_dataset

if os.path.exists("training"):
    shutil.rmtree("training")

if os.path.exists("validation"):
    shutil.rmtree("validation")

if os.path.exists("testing"):
    shutil.rmtree("testing")

split_dataset(
    dataset="simplified",
    task="regression",
    splits=(0.8, 0.2, 0.0),
    destination=".",
    shuffle=True,
    file_based_split=True,
)
