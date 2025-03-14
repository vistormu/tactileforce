import queue

import numpy as np

from panda import Panda
from src import (
    Server,
    ansi,
)

HOME_POS = (0.62, -0.30, 0.60)
HOME_ORI = (0.5, 0.5, 0.5, 0.5)


def get(data: queue.Queue):
    try:
        return data.get_nowait()
    except queue.Empty:
        return None


def main() -> None:
    panda = Panda(rate=10)
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
    filt_f = f
    alpha = 0.75

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

            while not data_queue.empty():
                data = data_queue.get()

                f = np.array([
                    data["fz"],
                    -data["fx"],
                    -data["fy"],
                ])

            filt_f = alpha * f + (1 - alpha) * filt_f

            state, err = panda.step()
            if err is not None:
                raise err

            delta_pos = filt_f / 500

            current_attractor = state.end_effector_position
            new_attractor = current_attractor + delta_pos
            distance = np.linalg.norm(new_attractor-current_attractor)

            if distance > 0.05:
                continue

            print(
                f"{ansi.BOLD}{ansi.GREEN}-> updated attractor{ansi.RESET}",
                f"   |> from: {current_attractor}",
                f"   |> to:   {new_attractor}",
                f"   |> distance: {distance:.4f}m",
                sep="\n",
                end="\n\n",
            )

            panda.go_to_pose(
                position=new_attractor.tolist(),
                orientation=HOME_ORI,
                duration=0.05,
            )

        except:
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
