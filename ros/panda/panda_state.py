import numpy as np
from dataclasses import dataclass


@dataclass
class PandaState:
    end_effector_position: np.ndarray
    end_effector_orientation: np.ndarray
    configuration: np.ndarray
    gripper_width: float

    @staticmethod
    def zero():
        return PandaState(
            end_effector_position=np.zeros(3),
            end_effector_orientation=np.zeros(4),
            configuration=np.zeros(7),
            gripper_width=0,
        )

    def __repr__(self) -> str:
        return f"""\033[2J\033[H
PANDA STATE
-----------
-> end effector position: 
   |> x: {self.end_effector_position[0]:.3f} m
   |> y: {self.end_effector_position[1]:.3f} m
   |> z: {self.end_effector_position[2]:.3f} m

-> end effector orientation: 
   |> w: {self.end_effector_orientation[0]:.2f}
   |> x: {self.end_effector_orientation[1]:.2f}
   |> y: {self.end_effector_orientation[2]:.2f}
   |> z: {self.end_effector_orientation[3]:.2f}

-> robot configuration:
   |> q1: {self.configuration[0]:.2f} rad | {self.configuration[0]/np.pi*180:.2f} deg
   |> q2: {self.configuration[1]:.2f} rad | {self.configuration[1]/np.pi*180:.2f} deg
   |> q3: {self.configuration[2]:.2f} rad | {self.configuration[2]/np.pi*180:.2f} deg
   |> q4: {self.configuration[3]:.2f} rad | {self.configuration[3]/np.pi*180:.2f} deg
   |> q5: {self.configuration[4]:.2f} rad | {self.configuration[4]/np.pi*180:.2f} deg
   |> q6: {self.configuration[5]:.2f} rad | {self.configuration[5]/np.pi*180:.2f} deg
   |> q7: {self.configuration[6]:.2f} rad | {self.configuration[6]/np.pi*180:.2f} deg

-> gripper configuration:
   |> {self.gripper_width:.3f} m
"""
