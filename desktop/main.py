import queue
import time
import argparse

import numpy as np

from src import (
    Server,
    Plotter,
    load_config,
    Data,
    ansi,
    Model,
    Client,
)


def get(data: queue.Queue):
    try:
        return data.get_nowait()
    except queue.Empty:
        return None


def train_model(model,
                trained_until: int,
                data_len: int,
                max_samples: int,
                data: Data,
                target: str | list[str],
                ) -> None:
    if model.is_training:
        return

    slc = slice(trained_until, data_len)
    if data_len - trained_until > max_samples:
        slc = slice(-max_samples, None)

    x = np.array([
        data["s0"][slc] / 100,
        data["s1"][slc] / 100,
        data["s2"][slc] / 100,
        data["s3"][slc] / 100,
    ]).T

    if isinstance(target, str):
        y = data[target][slc]
    else:
        y = np.array([data[t][slc] for t in target]).T

    model.start(x, y)


def main(config_path: str) -> None:
    config = load_config(config_path)

    # queue for data exchange between server and plotter
    data_queue = queue.Queue()
    event_queue = queue.Queue()

    # server
    server = Server(data_queue, event_queue, config.server.timeout)
    server.start(config.server.ip, config.server.port)

    # plots
    plotter = Plotter(config)

    # data
    data = Data(config.data.path, config.data.save, config.data.date_format)

    # model
    model = None
    fx_model = None
    fy_model = None
    fz_model = None

    if config.model.single_model:
        model = Model(config.model)
    else:
        fx_model = Model(config.model)
        fy_model = Model(config.model)
        fz_model = Model(config.model)

    trained_until = 0
    predicted_until = 0

    # client
    client = Client(config.client.ip, config.client.port) if config.client.control else None

    learning_time_exceeded = False
    start_time = time.time()
    client_connected = False

    while True:
        try:
            event = get(event_queue)

            # continue until a client connects
            if event != "connected" and not client_connected:
                plotter.draw()
                continue

            # client has just connected
            if event == "connected" and not client_connected:
                client_connected = True

                trained_until = 0
                predicted_until = 0

                learning_time_exceeded = False
                start_time = time.time()

                data.clear()
                plotter.clear()

            # client has just disconnected
            if event == "disconnected" and client_connected:
                client_connected = False

                data.save()
                plotter.save()

                if model is not None:
                    model.close()

                if fx_model is not None:
                    fx_model.close()

                if fy_model is not None:
                    fy_model.close()

                if fz_model is not None:
                    fz_model.close()

                continue

            # while client is connected
            while not data_queue.empty():
                data.update(data_queue.get())

            data_len = len(data)

            # update plot with prediction
            input_data = np.array([
                data["s0"][predicted_until:] / 100,
                data["s1"][predicted_until:] / 100,
                data["s2"][predicted_until:] / 100,
                data["s3"][predicted_until:] / 100,
            ]).T

            fx_pred = np.array([])
            fy_pred = np.array([])
            fz_pred = np.array([])

            if model is not None:
                f_pred = model.predict(input_data).T
                fx_pred = f_pred[0]
                fy_pred = f_pred[1]
                fz_pred = f_pred[2]

            if fx_model is not None:
                fx_pred = fx_model.predict(input_data)

            if fy_model is not None:
                fy_pred = fy_model.predict(input_data)

            if fz_model is not None:
                fz_pred = fz_model.predict(input_data)

            if fx_pred.ndim > 0 and len(fx_pred) > 0:
                data.update_numpy({
                    "fx_pred": fx_pred,
                    "fy_pred": fy_pred,
                    "fz_pred": fz_pred,
                })

            predicted_until = data_len
            plotter.update(data)

            # training stopped
            if time.time()-start_time > config.model.learning_time:
                # switch to hard inference
                if not learning_time_exceeded:
                    print(
                        f"{ansi.BOLD}{ansi.YELLOW}-> learning time exceeded{ansi.RESET}",
                        "   |> switching to hard inference",
                        "   |> sending force data to server" if config.client.control else "",
                        sep="\n",
                        end="\n\n",
                    )

                    if model is not None:
                        model.close()

                    if fx_model is not None:
                        fx_model.close()

                    if fy_model is not None:
                        fy_model.close()

                    if fz_model is not None:
                        fz_model.close()

                    learning_time_exceeded = True

                # send force data to server
                client.send_data({
                    "fx": data["fx_pred"][-1],
                    "fy": data["fy_pred"][-1],
                    "fz": data["fz_pred"][-1],
                    # "fx": data["fx"][-1],
                    # "fy": data["fy"][-1],
                    # "fz": data["fz"][-1],
                }) if client is not None else None

                continue

            # training
            if data_len - trained_until < config.model.required_samples:
                continue

            if model is not None:
                train_model(model, trained_until, data_len, config.model.max_samples, data, ["fx", "fy", "fz"])

            if fx_model is not None:
                train_model(fx_model, trained_until, data_len, config.model.max_samples, data, "fx")

            if fy_model is not None:
                train_model(fy_model, trained_until, data_len, config.model.max_samples, data, "fy")

            if fz_model is not None:
                train_model(fz_model, trained_until, data_len, config.model.max_samples, data, "fz")

        except KeyboardInterrupt:
            print(
                f"{ansi.BOLD}{ansi.YELLOW}-> user interrupt{ansi.RESET}",
                "   |> closing server",
                "   |> closing plotter",
                sep="\n",
                end="\n\n",
            )

            break

    server.stop()
    plotter.close()

    if model is not None:
        model.close()

    if fx_model is not None:
        fx_model.close()

    if fy_model is not None:
        fy_model.close()

    if fz_model is not None:
        fz_model.close()

    if client is not None:
        client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str)
    args = parser.parse_args()

    main(args.config)
