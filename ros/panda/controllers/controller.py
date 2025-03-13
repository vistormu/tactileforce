from abc import ABC, abstractmethod
from typing import Sequence, Tuple
import numpy as np


class Controller(ABC):
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def set_pose(self, position: Sequence[float], orientation: Sequence[float]) -> None:
        pass

    @abstractmethod
    def go_to_pose(self, position: Sequence[float], orientation: Sequence[float], duration: float) -> None:
        pass

    @abstractmethod
    def get_configuration(self) -> np.ndarray:
        pass

    @abstractmethod
    def get_end_effector_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        pass
