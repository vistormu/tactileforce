import datetime
import os
from dataclasses import dataclass

from matplotlib.axes import Axes
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from . import ansi
from .config import Config
from .data import Data


@dataclass
class AxInfo:
    ax: Axes
    x: str
    y: list[str]
    lines: list
    window: int

    def update(self, t: np.ndarray, y: list[np.ndarray]) -> None:
        # left pad with zeros if the new data is smaller than the window
        if len(t) < self.window:
            t = np.pad(t, (self.window - len(t), 0), mode="constant")
            y = [np.pad(y_, (self.window - len(y_), 0), mode="constant") for y_ in y]
        else:
            t = t[-self.window:]
            y = [y_[-self.window:] for y_ in y]

        for i in range(len(self.y)):
            self.lines[i].set_xdata(t)
            self.lines[i].set_ydata(y[i])

        self.ax.relim()
        self.ax.autoscale_view(True, True, True)

    def clear(self) -> None:
        for i in range(len(self.y)):
            self.lines[i].set_ydata(np.zeros(self.window))
            self.lines[i].set_xdata(np.zeros(self.window))


class Plotter:
    def __init__(self, config: Config) -> None:
        self.save_ = config.figure.save
        self.path = config.figure.path
        self.date_format = config.figure.date_format
        self.format = config.figure.format

        if not os.path.exists(self.path) and self.save_:
            print(
                f"{ansi.BOLD}{ansi.YELLOW_BRIGHT}-> specified path does not exist{ansi.RESET}",
                f"   |> path: {self.path}",
                "   |> data will not be saved",
                sep="\n",
                end="\n\n",
            )

            self.save_ = False

        window = int(config.plot.time_window / config.plot.dt)

        rows, cols = map(int, config.plot.layout.split("x"))

        # init plots
        plt.figure(figsize=config.plot.size)
        plt.tight_layout()
        gs = gridspec.GridSpec(rows, cols)

        self.axes = []
        for ax_info in config.plot.axes:
            location = ax_info.location.replace(":", "slice(None)")
            location = eval(location)
            ax = plt.subplot(gs[location])

            x = np.zeros(window)
            y = [np.zeros(window) for _ in ax_info.y]

            lines = []
            for i in range(len(ax_info.y)):
                line, = ax.plot(x, y[i], label=ax_info.y[i], color=ax_info.colors[i])
                lines.append(line)

            ax.set_title(ax_info.title)
            ax.set_ylabel(ax_info.ylabel)
            ax.set_xlabel(ax_info.xlabel)

            # 10% of the range as padding
            p = config.plot.padding / 100
            y_lower = ax_info.limits[0] - p * (ax_info.limits[1] - ax_info.limits[0])
            y_upper = ax_info.limits[1] + p * (ax_info.limits[1] - ax_info.limits[0])
            ax.set_ylim(y_lower, y_upper)

            # set number of ticks
            ax.yaxis.set_major_locator(plt.MaxNLocator(ax_info.n_ticks))  # type: ignore

            ax.grid(alpha=0.5)
            ax.legend()

            ax.autoscale_view(True, True, True)

            self.axes.append(AxInfo(
                ax=ax,
                x=ax_info.x,
                y=ax_info.y,
                lines=lines,
                window=window,
            ))

    def update(self, data: Data) -> None:
        plt.ion()

        for ax in self.axes:
            ax.update(
                data[ax.x],
                [data[s] for s in ax.y],
            )

        self.draw()

    def draw(self) -> None:
        plt.draw()
        plt.pause(0.001)

    def save(self) -> None:
        if not self.save_:
            return

        date = datetime.datetime.now().strftime(self.date_format)
        filename = os.path.join(self.path, f"{date}.{self.format}")
        plt.savefig(filename)

        print(
            f"{ansi.BOLD}{ansi.CYAN}-> figure saved{ansi.RESET}",
            f"   |> path: {filename}",
            sep="\n",
            end="\n\n",
        )

    def clear(self) -> None:
        for ax in self.axes:
            ax.clear()

    def close(self):
        plt.ioff()
        plt.close()
