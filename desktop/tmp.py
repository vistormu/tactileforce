import torch
import pandas as pd
import gpytorch
import math
import matplotlib.pyplot as plt
import os
import random
import numpy as np

#########################################
# 1. Data Loading
#########################################


def load_data(train_csv, val_csv, feature_columns, target_columns):
    # Load training data
    train_df = pd.read_csv(train_csv)
    train_x = torch.tensor(train_df[feature_columns].values, dtype=torch.float32)
    # Ensure targets are of shape (n_points, n_tasks)
    train_y = torch.tensor(train_df[target_columns].values, dtype=torch.float32)

    # Load validation data
    val_df = pd.read_csv(val_csv)
    val_x = torch.tensor(val_df[feature_columns].values, dtype=torch.float32)
    val_y = torch.tensor(val_df[target_columns].values, dtype=torch.float32)

    return train_x, train_y, val_x, val_y

#########################################
# 2. Define the Multitask Exact GP Model
#########################################


class MultitaskGPModel(gpytorch.models.ExactGP):
    def __init__(self, train_x, train_y, likelihood, num_tasks=3):
        """
        Args:
            train_x (Tensor): Training features of shape (n, d)
            train_y (Tensor): Training targets of shape (n, num_tasks)
            likelihood: The multitask likelihood
            num_tasks (int): Number of output tasks (default: 3)
        """
        super(MultitaskGPModel, self).__init__(train_x, train_y, likelihood)
        self.num_tasks = num_tasks

        # Use a multitask mean module (with one constant per task)
        self.mean_module = gpytorch.means.MultitaskMean(
            gpytorch.means.ConstantMean(), num_tasks=num_tasks
        )
        # Use a multitask kernel that applies an RBF kernel to the inputs and learns a task covariance.
        self.covar_module = gpytorch.kernels.MultitaskKernel(
            gpytorch.kernels.RBFKernel(), num_tasks=num_tasks, rank=1
        )

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        # Returns a MultitaskMultivariateNormal
        return gpytorch.distributions.MultitaskMultivariateNormal(mean_x, covar_x)

#########################################
# 3. Training and Validation Functions
#########################################


def train_gp(model, likelihood, train_x, train_y, optimizer, mll):
    model.train()
    likelihood.train()
    optimizer.zero_grad()
    output = model(train_x)
    loss = -mll(output, train_y)
    loss.backward()
    optimizer.step()
    return loss.item()


def validate_gp(model, likelihood, val_x, val_y):
    model.eval()
    likelihood.eval()
    with torch.no_grad(), gpytorch.settings.fast_pred_var():
        preds = likelihood(model(val_x))
        # Compute mean squared error over all tasks and examples
        mse = torch.mean((preds.mean - val_y)**2).item()
    return mse, preds.mean

#########################################
# 4. Main Function
#########################################


def main():
    # Settings
    train_csv = "datasets/squishy-simplified/training/please.csv"
    val_csv = "datasets/squishy-simplified/validation/please.csv"
    feature_columns = ["s0", "s1", "s2", "s3"]
    target_columns = ["x", "y", "fz"]

    num_epochs = 1000
    learning_rate = 0.05  # GP training may benefit from a higher LR
    best_val_mse = math.inf
    best_model_path = "best_gp_model.pth"
    best_likelihood_path = "best_gp_likelihood.pth"

    # Load data
    train_x, train_y, val_x, val_y = load_data(train_csv, val_csv, feature_columns, target_columns)
    train_x = train_x / 100  # Normalize inputs

    # Initialize the multitask likelihood and model
    num_tasks = len(target_columns)
    likelihood = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=num_tasks)
    model = MultitaskGPModel(train_x, train_y, likelihood, num_tasks=num_tasks)

    # Use the Adam optimizer
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Marginal log likelihood
    mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)

    # Training loop
    for epoch in range(num_epochs):
        loss = train_gp(model, likelihood, train_x, train_y, optimizer, mll)
        val_mse, _ = validate_gp(model, likelihood, val_x, val_y)
        print(f"Epoch {epoch+1}/{num_epochs}  Training Loss: {loss:.3f}  Val MSE: {val_mse:.4f}", end="\r")

        # Save the best model based on validation MSE
        if val_mse < best_val_mse:
            best_val_mse = val_mse
            torch.save(model.state_dict(), best_model_path)
            torch.save(likelihood.state_dict(), best_likelihood_path)

    # Load best model for inference
    model.load_state_dict(torch.load(best_model_path))
    likelihood.load_state_dict(torch.load(best_likelihood_path))
    model.eval()
    likelihood.eval()

    with torch.no_grad(), gpytorch.settings.fast_pred_var():
        preds = likelihood(model(val_x))
        predictions = preds.mean  # Tensor of shape (n_val, num_tasks)

    # r2 for each task
    def r2(y_true, y_pred):
        ss_res = torch.sum((y_true - y_pred)**2, dim=0)
        ss_tot = torch.sum((y_true - torch.mean(y_true, dim=0))**2, dim=0)
        return 1 - ss_res / ss_tot

    r2_scores = r2(val_y, predictions)
    for i, task in enumerate(target_columns):
        print(f"R2 {task}: {r2_scores[i]:.4f}")

    data_dir = "datasets/squishy-full/data/"
    files = os.listdir(data_dir)
    file = random.choice(files)

    df = pd.read_csv(os.path.join(data_dir, file))

    from_ = 0
    # to_ = len(df)
    to_ = 10_000
    s0 = df["s0"].to_numpy()[from_:to_]
    s1 = df["s1"].to_numpy()[from_:to_]
    s2 = df["s2"].to_numpy()[from_:to_]
    s3 = df["s3"].to_numpy()[from_:to_]
    fz = df["fz"].to_numpy()[from_:to_]
    x = df["x"].to_numpy()[from_:to_]
    y = df["y"].to_numpy()[from_:to_]

    fz_pred = []
    x_pred = []
    y_pred = []
    for i in range(len(fz)):
        if s0[i] == 0 and s1[i] == 0 and s2[i] == 0 and s3[i] == 0:
            fz_pred.append(np.nan)
            x_pred.append(np.nan)
            y_pred.append(np.nan)
            continue

        input = torch.tensor([[s0[i], s1[i], s2[i], s3[i]]], dtype=torch.float32) / 100
        prediction = likelihood(model(input))
        predictions = prediction.mean
        fz_pred.append(predictions[0][2].item())
        x_pred.append(predictions[0][0].item())
        y_pred.append(predictions[0][1].item())

    fz_pred = np.array(fz_pred)
    x_pred = np.array(x_pred)
    y_pred = np.array(y_pred)

    # def r2_score(y_true, y_pred):
    #     ss_res = np.sum((y_true - y_pred) ** 2)
    #     ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    #     r2 = 1 - (ss_res / ss_tot)
    #     return r2

    # print("R^2 Scores:")
    # print(f"Fz: {r2_score(fz, fz_pred)}")
    # print(f"X: {r2_score(x, x_pred)}")
    # print(f"Y: {r2_score(y, y_pred)}")

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
    main()
