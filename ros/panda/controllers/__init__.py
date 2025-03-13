from .controller import Controller
from .giovanni_controller import GiovanniController


def get_controller(id: str) -> Controller:
    if id.lower() == "giovanni":
        return GiovanniController()
    else:
        raise ValueError("wrong controller id")
