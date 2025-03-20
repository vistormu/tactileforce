import queue
import sys

import numpy as np

from panda import Panda
from src import (
    Server,
    ansi,
    load_config,
)


def get(data: queue.Queue):
    try:
        return data.get_nowait()
    except queue.Empty:
        return None


def main() -> None:
    # config
    config = load_config()

    # initialize panda
    panda = Panda(rate=10)
    panda.start("giovanni")
    panda.set_stiffness(
        translational=[config.panda.translational_stiffness]*3,
        rotational=[config.panda.rotational_stiffness]*3,
        nullspace=config.panda.nullspace_stiffness,
    )

    # homing
    panda.go_to_pose(
        position=config.panda.home_pos,
        orientation=config.panda.home_ori,
        duration=2.0,
    )
    if config.panda.use_gripper:
        panda.grasp(0.08, 0.05, 5)
        input("press any key to continue")
        panda.grasp(0.3, 0.05, 5)
        sys.stdin.flush()
        sys.stdout.flush()

    # queues
    data_queue = queue.Queue()
    event_queue = queue.Queue()

    # server
    server = Server(data_queue, event_queue, config.server.timeout)
    server.start(host=config.server.ip, port=config.server.port)

    # variables
    client_connected = False
    data = {}
    f = np.array([0, 0, 0])
    filt_f = f

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

            filt_f = config.force.alpha * f + (1 - config.force.alpha) * filt_f

            state, err = panda.step()
            if err is not None:
                raise err

            delta_pos = filt_f / np.array([config.force.fx_res, config.force.fy_res, config.force.fz_res])

            current_attractor = state.end_effector_position
            new_attractor = current_attractor + delta_pos
            distance = np.linalg.norm(new_attractor-current_attractor)

            if distance > config.force.valid_radius:
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
                orientation=config.panda.home_ori,
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

            if config.panda.use_gripper:
                panda.grasp(0.08, 0.1, 5)

            panda.close()
            server.stop()

            return


if __name__ == "__main__":
    main()
