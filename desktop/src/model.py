import threading
import time
from copy import deepcopy

import numpy as np

from catasta.models import GPRegressor, FeedforwardRegressor, TransformerRegressor

import torch
from torch.utils.data import DataLoader, TensorDataset
from torch.optim import AdamW

from gpytorch.mlls import VariationalELBO

from .import ansi
from .config import ModelConfig


class Model:
    def __init__(self, config: ModelConfig) -> None:
        # self.train_model = GPRegressor(
        #     n_inducing_points=config.n_inducing_points,
        #     n_inputs=len(config.features),
        #     n_outputs=len(config.targets),
        #     kernel=config.kernel,
        #     mean=config.mean,
        # )
        # self.train_model.train()

        self.train_model = FeedforwardRegressor(
            n_inputs=len(config.features),
            # n_outputs=len(config.targets),
            n_outputs=1,
            hidden_dims=[16, 16, 16],
            dropout=0.4,
        )
        self.train_model.train()

        # self.train_model = TransformerRegressor(
        #     n_inputs=len(config.features),
        #     n_outputs=len(config.targets),
        #     n_patches=1,
        #     d_model=32,
        #     n_layers=3,
        #     n_heads=2,
        #     feedforward_dim=16,
        #     head_dim=8,
        #     dropout=0.2,
        # )
        # self.train_model.train()

        self.inference_model = deepcopy(self.train_model)
        self.inference_model.load_state_dict(self.train_model.state_dict())
        self.inference_model.eval()

        self.training_thread = None
        self.is_training = False

        self.epochs = config.epochs
        self.batch_size = config.batch_size
        self.lr = config.lr
        self.tau = 0.95

    def start(self, x: np.ndarray, y: np.ndarray) -> None:
        self.training_thread = threading.Thread(
            target=self.train,
            args=(x, y),
        )
        self.training_thread.start()

    def close(self) -> None:
        if self.training_thread is not None and self.training_thread.is_alive():
            self.training_thread.join()

    def update_inference_model(self, mode: str) -> None:
        if mode == "soft":
            with torch.no_grad():
                for target_param, param in zip(self.inference_model.parameters(), self.train_model.parameters()):
                    target_param.copy_(self.tau * param + (1 - self.tau) * target_param)
        elif mode == "hard":
            self.inference_model.load_state_dict(self.train_model.state_dict())

    def train(self, x: np.ndarray, y: np.ndarray) -> None:
        """
        x: [n_samples, n_features]
        y: [n_samples, n_targets]
        """
        self.is_training = True

        # Prepare data
        x_train = torch.tensor(x, dtype=torch.float32)
        y_train = torch.tensor(y, dtype=torch.float32)

        print(
            f"{ansi.BOLD}{ansi.BLUE_BRIGHT}-> training model{ansi.RESET}",
            f"   |> x: {x_train.shape}",
            f"   |> y: {y_train.shape}",
            sep="\n",
        )

        dataset = TensorDataset(x_train, y_train)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        # Set up loss function and optimizer for the training model
        # loss_fn = VariationalELBO(self.train_model.likelihood, self.train_model, num_data=len(dataset))
        loss_fn = torch.nn.MSELoss()
        optimizer = AdamW(self.train_model.parameters(), lr=self.lr)

        # Set training mode
        self.train_model.train()

        start = time.time()
        for epoch in range(self.epochs):
            for x_batch, y_batch in dataloader:
                optimizer.zero_grad(set_to_none=True)

                y_batch = y_batch.squeeze(-1)

                output = self.train_model(x_batch)
                # loss = -loss_fn(output, y_batch)  # type: ignore
                loss = loss_fn(output, y_batch)  # type: ignore

                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.train_model.parameters(), 1.0)

                optimizer.step()

            self.update_inference_model("soft")

        # self.update_inference_model("hard")

        self.is_training = False

        print(
            f"   |> duration: {time.time() - start:.2f} s\n",
            end="\n\n",
        )

    @torch.no_grad()
    def predict(self, x: np.ndarray) -> np.ndarray:
        """
        x: [n_samples, n_features]
        Returns the prediction mean and standard deviation from the inference model.
        """
        input_tensor = torch.tensor(x, dtype=torch.float32)
        # output = self.inference_model.likelihood(self.inference_model(input_tensor))
        output = self.inference_model(input_tensor)

        # return output.mean.detach().numpy().astype(float)
        return output.detach().numpy().astype(float)
