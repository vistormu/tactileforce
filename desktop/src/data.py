import os
import datetime
import pandas as pd
import numpy as np

from . import ansi


class Data:
    def __init__(self, path: str, save: bool, date_format: str) -> None:
        self.data: dict[str, list[float]] = {}
        self.save_ = save
        self.date_format = date_format
        self.unkown_keys = set()

        self.path = path
        if not os.path.exists(self.path) and self.save_:
            print(
                f"{ansi.BOLD}{ansi.YELLOW_BRIGHT}-> specified path does not exist{ansi.RESET}",
                f"   |>{self.path}",
                "   |> data will not be saved",
                sep="\n",
                end="\n\n",
            )
            self.save_ = False

    def update(self, d: dict[str, float]) -> None:
        for k, v in d.items():
            if k in self.data:
                self.data[k].append(v)
            else:
                self.data[k] = [v]

    def update_numpy(self, d: dict[str, np.ndarray]) -> None:
        for k, v in d.items():
            if k in self.data:
                self.data[k].extend(v)
            else:
                self.data[k] = list(v)

    def save(self) -> None:
        if not self.save_ or not self.data:
            return

        date = datetime.datetime.now().strftime(self.date_format)
        filename = os.path.join(self.path, f"{date}.csv")
        pd.DataFrame(self.data).to_csv(filename, index=False)

        print(
            f"{ansi.BOLD}{ansi.GREEN}-> data saved{ansi.RESET}\n",
            f"   |> path: {filename}\n",
            sep="",
        )

    def clear(self) -> None:
        self.data.clear()

    def __getitem__(self, key: str) -> np.ndarray:
        data = self.data.get(key, [])
        if not data and key not in self.unkown_keys:
            self.unkown_keys.add(key)
            print(
                f"{ansi.BOLD}{ansi.YELLOW}-> unknown key recieved{ansi.RESET}\n",
                f"   |> name: {key}\n",
                sep="",
            )

        return np.array(data)

    def __len__(self) -> int:
        lengths = [len(v) for v in self.data.values()]

        # if not np.all(np.array(lengths) == lengths[0]):
        #     print(
        #         f"{ansi.BOLD}{ansi.YELLOW}-> data length mismatch{ansi.RESET}",
        #     )
        #     for k, v in self.data.items():
        #         print(f"   |> {k}: {len(v)}")
        #     print()

        return lengths[0]
