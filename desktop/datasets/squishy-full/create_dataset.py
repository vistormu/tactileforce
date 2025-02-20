from catasta.utils import split_dataset


split_dataset(
    dataset="data",
    task="regression",
    splits=(0.8, 0.2, 0.0),
    destination=".",
    shuffle=True,
    file_based_split=True,
)
