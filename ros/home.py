from panda import Panda


def home() -> None:
    panda = Panda(rate=10)

    panda.start("giovanni")
    panda.home()
