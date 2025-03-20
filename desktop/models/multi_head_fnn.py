import torch
from torch import Tensor
from torch.nn import (
    Module,
    Linear,
    Sequential,
    ReLU,
    Sigmoid,
    Tanh,
    GELU,
    LayerNorm,
    Dropout,
    BatchNorm1d,
    ModuleDict,
)


def get_actvation_function(activation: str) -> Module:
    match activation:
        case 'relu':
            return ReLU()
        case 'sigmoid':
            return Sigmoid()
        case 'tanh':
            return Tanh()
        case 'gelu':
            return GELU()
        case _:
            raise ValueError(f'Activation function {activation} not supported')


class MultiHeadFeedforwardRegressor(Module):
    def __init__(self, *,
                 n_inputs: int,
                 n_outputs: int,
                 dropout: float,
                 hidden_dims: list[int] = [],
                 use_layer_norm: bool = True,
                 use_batch_norm: bool = False,
                 activation: str = 'relu',
                 ) -> None:
        """
        feedforward regressor

        arguments
        ---------
        n_inputs: int
            number of input features
        n_outputs: int
            number of output features
        dropout: float
            dropout rate
        hidden_dims: list[int]
            hidden layer dimensions
        use_layer_norm: bool
            use layer normalization
        use_batch_norm: bool
            use batch normalization
        activation: str
            activation function. options: relu, sigmoid, tanh, gelu
        """
        super().__init__()

        layers: list[Module] = []

        # no hidden layers
        if not hidden_dims:
            self.net = Sequential(Linear(n_inputs, 1))
            return

        # hidden layers
        layers.append(Linear(n_inputs, hidden_dims[0]))
        n_layers = len(hidden_dims)

        for i in range(1, n_layers):
            # linear
            layers.append(Linear(hidden_dims[i-1], hidden_dims[i]))

            # batch norm
            if use_batch_norm:
                layers.append(BatchNorm1d(hidden_dims[i]))

            # layer norm
            if use_layer_norm:
                layers.append(LayerNorm(hidden_dims[i]))

            # activation
            layers.append(get_actvation_function(activation))

            # dropout
            layers.append(Dropout(dropout))

        # layers.append(Linear(hidden_dims[-1], n_outputs))

        # module dict with multihead
        self.heads = ModuleDict({
            f'head_{i}': Sequential(
                Linear(hidden_dims[-1], n_outputs),
            )
            for i in range(4)
        })

        self.net: Sequential = Sequential(*layers)

    def forward(self, x: Tensor, head: int = -1) -> Tensor:
        x = self.net(x)

        if head == -1:
            return torch.stack([head(x) for head in self.heads.values()]).mean(dim=0)

        return self.heads[f'head_{head}'](x).squeeze()
