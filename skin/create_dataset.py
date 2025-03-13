import os
import bisect
from collections import deque

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class MedianFilter:
    def __init__(self, window_size):
        self.window_size = window_size
        self.window = deque()
        self.sorted_window = []

    def append(self, value):
        self.window.append(value)
        bisect.insort(self.sorted_window, value)

        if len(self.window) > self.window_size:
            oldest_value = self.window.popleft()
            self.sorted_window.remove(oldest_value)

    def compute(self):
        n = len(self.sorted_window)
        if n == 0:
            return None  # No data in the window
        if n % 2 == 1:
            return self.sorted_window[n // 2]
        else:
            mid_index = n // 2
            return (self.sorted_window[mid_index - 1] + self.sorted_window[mid_index]) / 2

    def reset(self):
        self.window.clear()
        self.sorted_window.clear()


def append(df: pd.DataFrame, row: dict) -> pd.DataFrame:
    return pd.concat([df, pd.DataFrame(row, index=[0])], ignore_index=True)  # type: ignore


def extract_amplitudes(signal: np.ndarray) -> list[tuple[int, int, float]]:
    amplitudes = []
    in_pulse = False
    pulse_values = []
    start_index = 0

    for i, value in enumerate(signal):
        # start of a new pulse
        if not np.isnan(value) and not in_pulse:
            in_pulse = True
            pulse_values = [value]
            start_index = i

        # middle of a pulse
        elif not np.isnan(value) and in_pulse:
            pulse_values.append(value)

        # end of a pulse
        elif np.isnan(value) and in_pulse:
            median_amp = np.median(pulse_values)
            amplitudes.append((start_index, i, median_amp))
            in_pulse = False

    # last pulse
    if in_pulse:
        median_amp = np.median(pulse_values)
        amplitudes.append((start_index, len(signal) - 1, median_amp))

    return amplitudes


def main() -> None:
    # data
    data_dir = "datasets/squishy-skin/raw-data/simplified/"
    files = os.listdir(data_dir)
    files.sort()

    dfs_full = []
    dfs_simple = []

    path_simple = "datasets/squishy-skin/simplified/data.csv"
    path_full = "datasets/squishy-skin/full/data.csv"

    # positions
    forces = ["0.5N", "1.0N", "1.5N", "2.0N", "2.5N", "3.0N"]
    radii = [0.20, 0.35, 0.50, 0.65, 0.85, 1.00]
    positions = {
        "center": (0.0, 0.0),
        "right": (0.0, -1.0),
        "up_right": (1.0, -1.0),
        "up": (1.0, 0.0),
        "up_left": (1.0, 1.0),
        "left": (0.0, 1.0),
        "down_left": (-1.0, 1.0),
        "down": (-1.0, 0.0),
        "down_right": (-1.0, -1.0),
    }
    n_touchs = 2

    # =========
    # filtering
    # =========
    window_fz = 10
    window_s = 10
    threshold_fz = 0.11
    for i, file in enumerate(files):
        df = pd.read_csv(os.path.join(data_dir, file))

        fz = df["fz"].to_numpy()
        s0 = df["s0"].to_numpy()
        s1 = df["s1"].to_numpy()
        s2 = df["s2"].to_numpy()
        s3 = df["s3"].to_numpy()

        filter = MedianFilter(window_fz)
        for j in range(len(fz)):
            if fz[j] < threshold_fz:
                fz[j] = np.nan
                filter.reset()
                continue

            filter.append(fz[j])
            fz[j] = filter.compute()

        filter_s0 = MedianFilter(window_s)
        filter_s1 = MedianFilter(window_s)
        filter_s2 = MedianFilter(window_s)
        filter_s3 = MedianFilter(window_s)
        for j in range(len(s0)):
            if np.isnan(fz[j]):
                s0[j] = np.nan
                s1[j] = np.nan
                s2[j] = np.nan
                s3[j] = np.nan
                filter_s0.reset()
                filter_s1.reset()
                filter_s2.reset()
                filter_s3.reset()
                continue

            filter_s0.append(s0[j])
            s0[j] = filter_s0.compute()

            filter_s1.append(s1[j])
            s1[j] = filter_s1.compute()

            filter_s2.append(s2[j])
            s2[j] = filter_s2.compute()

            filter_s3.append(s3[j])
            s3[j] = filter_s3.compute()

        df["fz"] = fz
        df["s0"] = s0
        df["s1"] = s1
        df["s2"] = s2
        df["s3"] = s3
        df.drop(columns=["time"])

        dfs_full.append(df)

    # ======================================
    # extract amplitudes and create datasets
    # ======================================
    for i, df in enumerate(dfs_full):
        # force = forces[i % len(forces)]
        radius = radii[i // len(forces)]

        df_simple = pd.DataFrame()

        fz = df["fz"].to_numpy()
        s0 = df["s0"].to_numpy()
        s1 = df["s1"].to_numpy()
        s2 = df["s2"].to_numpy()
        s3 = df["s3"].to_numpy()
        x = np.zeros_like(fz)
        y = np.zeros_like(fz)

        fz_amps = extract_amplitudes(fz)
        s0_amps = extract_amplitudes(s0)
        s1_amps = extract_amplitudes(s1)
        s2_amps = extract_amplitudes(s2)
        s3_amps = extract_amplitudes(s3)

        # def check(amps: list[tuple[int, int, float]]) -> bool:
        #     return len(amps) == len(positions)*n_touchs

        # if not check(fz_amps) or not check(s0_amps) or not check(s1_amps) or not check(s2_amps) or not check(s3_amps):
        #     print(f"{i: }", len(fz_amps), len(s0_amps), len(s1_amps), len(s2_amps), len(s3_amps))

        position_idx = 0
        for j in range(len(positions)*n_touchs):
            start, end, fz_amp = fz_amps[j]
            _, _, s0_amp = s0_amps[j]
            _, _, s1_amp = s1_amps[j]
            _, _, s2_amp = s2_amps[j]
            _, _, s3_amp = s3_amps[j]

            position = list(positions.values())[position_idx]
            x_value = position[0] * radius
            y_value = position[1] * radius

            x[start:end] = x_value
            y[start:end] = y_value

            df_simple = append(df_simple, row={
                "x": x_value,
                "y": y_value,
                "fz": fz_amp,
                "s0": s0_amp,
                "s1": s1_amp,
                "s2": s2_amp,
                "s3": s3_amp,
            })

            if (j+1) % n_touchs == 0:
                position_idx += 1

        # end
        df["x"] = x
        df["y"] = y

        dfs_simple.append(df_simple)

    # ================
    # convert nan to 0
    # ================
    for df in dfs_full:
        df.fillna(0, inplace=True)

    # =============
    # save datasets
    # =============
    if save:
        df_full = pd.concat(dfs_full, ignore_index=True)
        if os.path.exists(path_full):
            os.remove(path_full)

        df_full.to_csv(path_full, index=False)

        df_simple = pd.concat(dfs_simple, ignore_index=True)
        if os.path.exists(path_simple):
            os.remove(path_simple)

        df_simple.to_csv(path_simple, index=False)

    # =============
    # plot datasets
    # =============
    if not plot:
        return

    red = "#cf7171"
    green = "#dbe8c1"
    blue = "#aecdd2"
    yellow = "#fadf7f"
    black = "#2f2f2f"
    for i, (df, df_simple) in enumerate(zip(dfs_full, dfs_simple)):
        force = forces[i % len(forces)]
        radius = radii[i // len(forces)]

        fig, axs = plt.subplots(3, 2, figsize=(12, 9))
        fig.suptitle(f"{radius} - {force}")

        # full
        axs[0][0].set_title("Force")
        axs[0][0].plot(df["fz"], color=black)
        axs[0][0].set_ylim(-0.1, 6.1)

        axs[1][0].set_title("Position")
        axs[1][0].plot(df["x"], color=red)
        axs[1][0].plot(df["y"], color=blue)
        axs[1][0].set_ylim(-1.1, 1.1)

        axs[2][0].set_title("Sensors")
        axs[2][0].plot(df["s0"], color=red)
        axs[2][0].plot(df["s1"], color=green)
        axs[2][0].plot(df["s2"], color=blue)
        axs[2][0].plot(df["s3"], color=yellow)
        # axs[2][0].set_ylim(-1.1, 1.1)

        # simplified
        axs[0][1].set_title("Force")
        axs[0][1].plot(df_simple["fz"], color=black, marker="o")
        axs[0][1].set_ylim(-0.1, 6.1)

        axs[1][1].set_title("Position")
        axs[1][1].plot(df_simple["x"], color=red, marker="o")
        axs[1][1].plot(df_simple["y"], color=blue, marker="o")
        axs[1][1].set_ylim(-1.1, 1.1)

        axs[2][1].set_title("Sensors")
        axs[2][1].plot(df_simple["s0"], color=red, marker="o")
        axs[2][1].plot(df_simple["s1"], color=green, marker="o")
        axs[2][1].plot(df_simple["s2"], color=blue, marker="o")
        axs[2][1].plot(df_simple["s3"], color=yellow, marker="o")
        # axs[2][1].set_ylim(-10, 30)

        for i in range(3):
            for j in range(2):
                axs[i][j].grid(alpha=0.5)

        plt.tight_layout()
        plt.show()


def test_dataset() -> None:
    path = "raw-data/squishy-test/"
    files = os.listdir(path)
    files.sort()

    dfs = []
    save_path = "datasets/squishy-test/data.csv"

    radii = [0.25, 0.5, 0.75, 1.0]
    positions = {
        "center": (0.0, 0.0),
        "right": (0.0, -1.0),
        "up_right": (1.0, -1.0),
        "up": (1.0, 0.0),
        "up_left": (1.0, 1.0),
        "left": (0.0, 1.0),
        "down_left": (-1.0, 1.0),
        "down": (-1.0, 0.0),
        "down_right": (-1.0, -1.0),
    }

    # ===================
    # calculate prosition
    # ===================
    for i, file in enumerate(files):
        radius = radii[i // len(positions)]
        position = list(positions.values())[i % len(positions)]

        df = pd.read_csv(os.path.join(path, file))

        fz = df["fz"].to_numpy()

        fz = np.where(fz < 0.15, 0, fz)

        x = np.zeros_like(fz)
        y = np.zeros_like(fz)

        for j in range(len(fz)):
            if fz[j] < 0.1:
                x[j] = 0
                y[j] = 0
                continue

            x[j] = position[0] * radius
            y[j] = position[1] * radius

        df["fz"] = fz
        df["x"] = x
        df["y"] = y

        df = df.drop(columns=["time", "x_pred", "y_pred", "fz_pred"])

        dfs.append(df)

    # =============
    # save datasets
    # =============
    if save:
        df = pd.concat(dfs, ignore_index=True)
        if os.path.exists(save_path):
            os.remove(save_path)

        df.to_csv(save_path, index=False)

    # =============
    # plot datasets
    # =============


if __name__ == "__main__":
    plot = False
    save = not plot
    main()
    # test_dataset()
