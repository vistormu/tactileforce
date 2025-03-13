from panda import Panda


def read() -> None:
    panda = Panda(rate=10)
    panda.start("giovanni")

    while True:
        state, err = panda.step()
        if err is not None:
            print(err)
            break

        print(state)


if __name__ == "__main__":
    read()
