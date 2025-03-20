from typing import NamedTuple, List

import tomli


class PandaConfig(NamedTuple):
    rate: int
    controller: str
    home_pos: List[float]
    home_ori: List[float]
    translational_stiffness: float
    rotational_stiffness: float
    nullspace_stiffness: float
    use_gripper: bool


class ServerConfig(NamedTuple):
    ip: str
    port: int
    timeout: int


class ForceConfig(NamedTuple):
    alpha: float
    fx_res: float
    fy_res: float
    fz_res: float
    valid_radius: float


class Config(NamedTuple):
    panda: PandaConfig
    server: ServerConfig
    force: ForceConfig


def load_config() -> Config:
    with open("configs/control.toml", "rb") as f:
        config = tomli.load(f)

    # panda
    panda = PandaConfig(
        rate=config["panda"]["rate"],
        controller=config["panda"]["controller"],
        home_pos=config["panda"]["home_pos"],
        home_ori=config["panda"]["home_ori"],
        translational_stiffness=config["panda"]["translational_stiffness"],
        rotational_stiffness=config["panda"]["rotational_stiffness"],
        nullspace_stiffness=config["panda"]["nullspace_stiffness"],
        use_gripper=config["panda"]["use_gripper"],
    )

    # server
    server = ServerConfig(
        ip=config["server"]["ip"],
        port=config["server"]["port"],
        timeout=config["server"]["timeout"],
    )

    # force
    force = ForceConfig(
        alpha=config["force"]["alpha"],
        fx_res=config["force"]["fx_res"],
        fy_res=config["force"]["fy_res"],
        fz_res=config["force"]["fz_res"],
        valid_radius=config["force"]["valid_radius"],
    )

    return Config(
        panda=panda,
        server=server,
        force=force,
    )
