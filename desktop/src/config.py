from typing import NamedTuple
import tomllib


# ======
# SERVER
# ======
class ServerConfig(NamedTuple):
    ip: str
    port: int
    timeout: float


# ======
# CLIENT
# ======
class ClientConfig(NamedTuple):
    ip: str
    port: int
    control: bool


# ====
# DATA
# ====
class DataConfig(NamedTuple):
    save: bool
    path: str
    date_format: str


# ======
# FIGURE
# ======
class FigureConfig(NamedTuple):
    save: bool
    path: str
    date_format: str
    format: str


# =====
# MODEL
# =====
class ModelConfig(NamedTuple):
    targets: list[str]
    features: list[str]
    required_samples: int
    max_samples: int
    epochs: int
    batch_size: int
    lr: float
    learning_time: int
    model: str
    single_model: bool
    tau: float
    hyperparameters: dict


# ====
# PLOT
# ====
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


# ======
# CONFIG
# ======
class Config(NamedTuple):
    server: ServerConfig
    client: ClientConfig
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
        required_samples=config["model"]["required_samples"],
        max_samples=config["model"]["max_samples"],
        epochs=config["model"]["epochs"],
        batch_size=config["model"]["batch_size"],
        lr=config["model"]["lr"],
        learning_time=config["model"]["learning_time"],
        model=config["model"]["model"],
        single_model=config["model"]["single_model"],
        tau=config["model"]["tau"],
        hyperparameters=config["model"]["hyperparameters"],
    )

    client = ClientConfig(
        ip=config["client"]["ip"],
        port=config["client"]["port"],
        control=config["client"]["control"],
    )

    return Config(
        server=server,
        data=data,
        figure=figure,
        plot=plot,
        model=model,
        client=client,
    )
