import queue

import numpy as np

from panda import Panda
from src import (
    Server,
    ansi,
)

HOME_POS = (0.62, -0.30, 0.60)
HOME_ORI = (0.5, 0.5, 0.5, 0.5)


def home() -> None:
    panda = Panda(rate=10)
    panda.start("giovanni")
    panda.go_to_pose(
        position=HOME_POS,
        orientation=HOME_ORI,
        duration=2.0,
    )
    panda.close()


def get(data: queue.Queue):
    try:
        return data.get_nowait()
    except queue.Empty:
        return None


def main() -> None:
    panda = Panda(rate=200)
    panda.start("giovanni")
    panda.go_to_pose(
        position=HOME_POS,
        orientation=HOME_ORI,
        duration=2.0,
    )

    data_queue = queue.Queue()
    event_queue = queue.Queue()

    server = Server(data_queue, event_queue, 2)
    server.start(host="auto", port=8080)

    client_connected = False
    data = {}
    f = np.array([0, 0, 0])
    last_f = None

    while True:
        try:
            event = get(event_queue)

            # continue until a client connects
            if event != "connected" and not client_connected:
                continue

            # client has just connected
            if event == "connected" and not client_connected:
                client_connected = True

            # client has just disconnected
            if event == "disconnected" and client_connected:
                client_connected = False
                continue

            if data_queue.empty() and last_f is not None:
                f = last_f

            elif not data_queue.empty():
                # while client is connected
                while not data_queue.empty():
                    data = data_queue.get()

                f = np.array([
                    data["fz"],
                    -data["fx"],
                    -data["fy"],
                ])

            last_f = f

            state, err = panda.step()
            if err is not None:
                print(err)
                break

            k_eff = np.array([200.0, 200.0, 200.0])

            delta_pos = f / k_eff

            current_attractor = state.end_effector_position
            new_attractor = current_attractor + delta_pos
            distance = np.linalg.norm(new_attractor-current_attractor)

            print(
                f"{ansi.BOLD}{ansi.GREEN}-> updated attractor{ansi.RESET}",
                f"   |> from: {current_attractor}",
                f"   |> to:   {new_attractor}",
                f"   |> distance: {distance:.4f}m",
                sep="\n",
                end="\n\n",
            )

            if distance > 0.01 and distance < 0.05:
                panda.go_to_pose(
                    position=new_attractor.tolist(),
                    orientation=HOME_ORI,
                    duration=0.2,
                )

        except KeyboardInterrupt:
            print(
                f"{ansi.BOLD}{ansi.YELLOW}-> user interrupt{ansi.RESET}",
                "   |> closing server",
                "   |> closing plotter",
                sep="\n",
                end="\n\n",
            )

            break

    panda.close()
    server.stop()


if __name__ == "__main__":
    # home()
    main()
