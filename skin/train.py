import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from catasta import Scaffold, Dataset, Foundation, Archway
from catasta.models import TransformerRegressor, GPRegressor
from catasta.dataclasses import EvalInfo
from catasta.transformations import Custom

from torch.nn import Module


class KalmanFilter:
    def __init__(self, process_variance: float, measurement_variance: float, initial_error_covariance: float, initial_estimate: float):
        """
        Initialize the Kalman filter.

        :param process_variance: The process (model) variance (q)
        :param measurement_variance: The measurement variance (r)
        :param initial_error_covariance: The initial error covariance (p)
        :param initial_estimate: The initial estimate (xHat)
        """
        self.q = process_variance
        self.r = measurement_variance
        self.p = initial_error_covariance
        self.f = 1.0  # State transition coefficient
        self.h = 1.0  # Observation model coefficient
        self.xHat = float(initial_estimate)

    def compute(self, measurement: float) -> float:
        """
        Perform a single Kalman filter update with the given measurement.

        :param measurement: The new measurement value.
        :return: The updated state estimate.
        """
        # Prediction step
        xHat_predict = self.f * self.xHat
        p_predict = self.f * self.p * self.f + self.q

        # Kalman gain calculation
        k = p_predict * self.h / (self.h * p_predict * self.h + self.r)

        # Update step
        self.xHat = xHat_predict + k * (float(measurement) - self.h * xHat_predict)
        self.p = (1 - k * self.h) * p_predict

        return self.xHat


class MultiKalmanFilter:
    def __init__(self, process_variance: float, measurement_variance: float, initial_error_covariance: float, initial_estimates: list[float]):
        """
        Initialize a collection of Kalman filters.

        :param process_variance: The process (model) variance (q) for each filter.
        :param measurement_variance: The measurement variance (r) for each filter.
        :param initial_error_covariance: The initial error covariance (p) for each filter.
        :param initial_estimates: A list of initial estimates, one per filter.
        """
        self.filters = [
            KalmanFilter(process_variance, measurement_variance, initial_error_covariance, est)
            for est in initial_estimates
        ]

    def compute(self, measurements: list[float]) -> list[float]:
        """
        Update each Kalman filter with the corresponding measurement.

        :param measurements: A list of measurement values, one per filter.
        :return: A list of updated state estimates.
        """
        results = []
        for kf, measurement in zip(self.filters, measurements):
            results.append(kf.compute(measurement))
        return results


class MultiMSELoss(Module):
    def __init__(self):
        super(MultiMSELoss, self).__init__()

    def forward(self, y_pred, y_true):
        loss = 0
        if len(y_pred.shape) == 1:
            y_pred = y_pred.unsqueeze(0)

        for i in range(y_pred.shape[1]):
            loss += (y_pred[:, i] - y_true[:, i]).pow(2).mean()

        return loss


def correlate_signals(signal: np.ndarray) -> np.ndarray:
    eps = 1e-6

    diff = signal[:, :, None] - signal[:, None, :]
    sum_ = signal[:, :, None] + signal[:, None, :]

    ratio = diff / (sum_ + eps)

    i_upper, j_upper = np.triu_indices(4, k=1)

    features = ratio[:, i_upper, j_upper]

    return features


def correlate_signals_log(signal: np.ndarray) -> np.ndarray:
    eps = 1e-6  # small constant to avoid taking log(0)

    log_signal = np.log(signal + eps)  # shape (n_data, 4)

    diff = log_signal[:, :, None] - log_signal[:, None, :]  # shape (n_data, 4, 4)

    i_upper, j_upper = np.triu_indices(4, k=1)
    features = diff[:, i_upper, j_upper]  # shape (n_data, 6)

    return features


def objective(params: dict, save_path: str = "", return_metrics: bool = False) -> float | EvalInfo:
    model = TransformerRegressor(
        n_inputs=4,
        n_outputs=3,
        n_patches=params["n_patches"],
        d_model=params["d_model"],
        n_heads=params["n_heads"],
        n_layers=params["n_layers"],
        feedforward_dim=params["feedforward_dim"],
        head_dim=params["head_dim"],
        dropout=params["dropout"],
    )

    # model = GPRegressor(
    #     n_inputs=4,
    #     n_outputs=3,
    #     n_inducing_points=params["n_inducing_points"],
    #     kernel=params["kernel"],
    #     mean=params["mean"],
    # )

    dataset = Dataset(
        task="regression",
        root="datasets/squishy-skin/",
        input_name=["s0", "s1", "s2", "s3"],
        output_name=["x", "y", "fz"],
        input_transformations=[
            Custom(lambda x: x / 100),
            # Custom(correlate_signals),
        ],
    )

    scaffold = Scaffold(
        model=model,
        dataset=dataset,
        optimizer="adamw",
        loss_function=MultiMSELoss(),
        # loss_function="variational_elbo",
        verbose=return_metrics,
    )

    scaffold.train(
        epochs=2_000,
        batch_size=params["batch_size"],
        lr=params["lr"],
    )

    metrics = scaffold.evaluate()

    if save_path:
        scaffold.save(save_path)

    return metrics.r2 if not return_metrics else metrics


def optimize() -> None:
    hyperparameters = {
        "n_patches": (1, 4),
        "d_model": (4, 8, 16, 32, 64),
        "n_heads": (1, 2),
        "n_layers": (1, 2),
        "feedforward_dim": (8, 16, 32, 64),
        "head_dim": (8, 16, 32, 64),
        "dropout": (0.0, 0.1, 0.2),
        "batch_size": (32, 64, 128),
        "lr": (1e-5, 1e-4, 1e-3),
    }

    foundation = Foundation(
        sampler="tpe",
        hyperparameter_space=hyperparameters,
        objective_function=objective,  # type: ignore
        direction="maximize",
        n_trials=20,
    )

    results = foundation.optimize()

    print(results)


def train() -> None:
    hyperparameters = {
        "n_patches": 4,
        "d_model": 64,
        "n_heads": 1,
        "n_layers": 2,
        "feedforward_dim": 16,
        "head_dim": 16,
        "dropout": 0.0,
        "batch_size": 32,
        "lr": 0.001,
    }

    # hyperparameters = {
    #     "n_inducing_points": 16,
    #     "kernel": "matern",
    #     "mean": "constant",
    #     "batch_size": 64,
    #     "lr": 1e-3,
    # }

    metrics = objective(
        params=hyperparameters,
        save_path="models/transformer.pt",
        return_metrics=True,
    )

    print(metrics)


def inference() -> None:
    data_path = "datasets/squishy-skin/simplified/data.csv"

    df = pd.read_csv(data_path)

    # from_ = 20_000
    # to_ = 100_000
    from_ = 0
    to_ = len(df)
    s0 = df["s0"].to_numpy()[from_:to_]
    s1 = df["s1"].to_numpy()[from_:to_]
    s2 = df["s2"].to_numpy()[from_:to_]
    s3 = df["s3"].to_numpy()[from_:to_]
    fz = df["fz"].to_numpy()[from_:to_]
    try:
        x = df["x"].to_numpy()[from_:to_]
        y = df["y"].to_numpy()[from_:to_]
    except KeyError:
        x = np.zeros_like(fz)
        y = np.zeros_like(fz)

    archway = Archway("models/transformer.pt")

    model_filter = MultiKalmanFilter(
        process_variance=0.1,
        measurement_variance=20.0,
        initial_error_covariance=20.0,
        initial_estimates=[0, 0, 0],
    )

    fz_preds = []
    x_preds = []
    y_preds = []
    for i in range(len(fz)):
        if s0[i] == 0 and s1[i] == 0 and s2[i] == 0 and s3[i] == 0:
            fz_preds.append(0)
            x_preds.append(0)
            y_preds.append(0)

            model_filter.compute([0, 0, 0])

            continue

        input = np.array([[s0[i], s1[i], s2[i], s3[i]]]).astype(np.float32)
        input = input / 100
        # input = correlate_signals(input)

        prediction = archway.predict(input)

        x_pred = prediction[0]
        y_pred = prediction[1]
        fz_pred = prediction[2]

        x_pred = np.clip(x_pred, -1, 1)
        y_pred = np.clip(y_pred, -1, 1)

        x_pred, y_pred, fz_pred = model_filter.compute([x_pred, y_pred, fz_pred])

        x_preds.append(x_pred)
        y_preds.append(y_pred)
        fz_preds.append(fz_pred)

    fz_pred = np.array(fz_preds)
    x_pred = np.array(x_preds)
    y_pred = np.array(y_preds)

    def r2_score(y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        return r2

    print("R^2 Scores:")
    print(f"Fz: {r2_score(fz, fz_pred)}")
    print(f"X: {r2_score(x, x_pred)}")
    print(f"Y: {r2_score(y, y_pred)}")

    fig, ax = plt.subplots(4, 1, figsize=(19, 8))
    ax[0].plot(fz, alpha=0.5, label="True")
    ax[0].plot(fz_pred, label="Predicted")
    ax[0].set_title("Fz")
    ax[0].set_xlabel("True")
    ax[0].set_ylabel("Predicted")
    ax[0].legend()

    ax[1].plot(x, alpha=0.5, label="True")
    ax[1].plot(x_pred, label="Predicted")
    ax[1].set_title("X")
    ax[1].set_xlabel("True")
    ax[1].set_ylabel("Predicted")
    ax[1].legend()

    ax[2].plot(y, alpha=0.5, label="True")
    ax[2].plot(y_pred, label="Predicted")
    ax[2].set_title("Y")
    ax[2].set_xlabel("True")
    ax[2].set_ylabel("Predicted")
    ax[2].legend()

    ax[3].plot(s0, label="S0")
    ax[3].plot(s1, label="S1")
    ax[3].plot(s2, label="S2")
    ax[3].plot(s3, label="S3")
    ax[3].set_title("Sensors")
    ax[3].legend()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # optimize()
    train()
    inference()
