from typing import NamedTuple
import tomllib


class AxisConfig(NamedTuple):
    location: str
    x: str
    y: list[str]
    xlabel: str
    ylabel: str
    colors: list[str]
    limits: tuple[float, float]
    title: str
    n_ticks: int


class PlotConfig(NamedTuple):
    layout: str
    time_window: int
    dt: float
    size: tuple[int, int]
    padding: float
    axes: list[AxisConfig]


class ServerConfig(NamedTuple):
    ip: str
    port: int
    timeout: float


class DataConfig(NamedTuple):
    save: bool
    path: str
    date_format: str


class FigureConfig(NamedTuple):
    save: bool
    path: str
    date_format: str
    format: str


class ModelConfig(NamedTuple):
    targets: list[str]
    features: list[str]
    n_inducing_points: int
    kernel: str
    mean: str
    required_samples: int
    max_samples: int
    epochs: int
    batch_size: int
    lr: float
    learning_time: int


class Config(NamedTuple):
    server: ServerConfig
    data: DataConfig
    figure: FigureConfig
    plot: PlotConfig
    model: ModelConfig


def load_config(path: str) -> Config:
    with open(path, "rb") as f:
        config = tomllib.load(f)

    colors = config.get("colors", {})

    server = ServerConfig(
        ip=config["server"]["ip"],
        port=config["server"]["port"],
        timeout=config["server"]["timeout"],
    )

    data = DataConfig(
        save=config["data"]["save"],
        path=config["data"]["path"],
        date_format=config["data"]["date_format"],
    )

    figure = FigureConfig(
        save=config["figure"]["save"],
        path=config["figure"]["path"],
        date_format=config["figure"]["date_format"],
        format=config["figure"]["format"],
    )

    # axes
    plot = PlotConfig(
        layout=config["plot"].pop("layout"),
        time_window=config["plot"].pop("time_window"),
        dt=config["plot"].pop("dt"),
        size=config["plot"].pop("size"),
        padding=config["plot"].pop("padding"),
        axes=[AxisConfig(
            location=name,
            x=config["plot"][name]["x"],
            y=config["plot"][name]["y"],
            xlabel=config["plot"][name]["xlabel"],
            ylabel=config["plot"][name]["ylabel"],
            colors=[colors.get(color, color) for color in config["plot"][name]["colors"]],
            limits=config["plot"][name]["limits"],
            title=config["plot"][name]["title"],
            n_ticks=config["plot"][name]["n_ticks"],
        ) for name in config["plot"].keys()],
    )

    # model
    model = ModelConfig(
        targets=config["model"]["targets"],
        features=config["model"]["features"],
        n_inducing_points=config["model"]["n_inducing_points"],
        kernel=config["model"]["kernel"],
        mean=config["model"]["mean"],
        required_samples=config["model"]["required_samples"],
        max_samples=config["model"]["max_samples"],
        epochs=config["model"]["epochs"],
        batch_size=config["model"]["batch_size"],
        lr=config["model"]["lr"],
        learning_time=config["model"]["learning_time"],
    )

    return Config(
        server=server,
        data=data,
        figure=figure,
        plot=plot,
        model=model,
    )
