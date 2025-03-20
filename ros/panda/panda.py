from typing import Union, Tuple, Sequence

import rospy

from .panda_state import PandaState
from .controllers import get_controller


class Panda:
    def __init__(self, rate: int) -> None:
        rospy.init_node("panda_node", anonymous=True)
        self.rate = rospy.Rate(rate)
        self.HOME_POSITION = [0.5, 0.0, 0.3]
        self.HOME_ORIENTATION = [0.0, 1.0, 0.0, 0.0]

    def start(self, mode: str) -> PandaState:
        self.controller = get_controller(mode)
        self.controller.start()
        rospy.sleep(0.3)

        configuration = self.controller.get_configuration()
        position, orientation = self.controller.get_end_effector_pose()
        gripper = self.controller.get_gripper_width()

        return PandaState(
            end_effector_position=position,
            end_effector_orientation=orientation,
            configuration=configuration,
            gripper_width=gripper,
        )

    def set_pose(self, position: Sequence[float], orientation: Sequence[float]) -> None:
        if len(position) != 3 and len(orientation) != 4:
            print("todo")
            return

        self.controller.set_pose(position, orientation)

    def go_to_pose(self, position: Sequence[float], orientation: Sequence[float], duration: float) -> None:
        if len(position) != 3 and len(orientation) != 4:
            print("todo")
            return

        if rospy.is_shutdown():
            print("shutdown")
            return

        self.controller.go_to_pose(position, orientation, duration)

    def grasp(self, width: float, speed: float, force: float) -> None:
        if width < 0 or width > 1:
            print("todo")
            return

        self.controller.grasp(width, speed, force)

    def set_stiffness(self, translational: Sequence[float], rotational: Sequence[float], nullspace: float) -> None:
        if len(translational) != 3:
            print("todo")
            return

        if len(rotational) != 3:
            print("todo")
            return

        self.controller.set_stiffness(translational, rotational, nullspace)

    def home(self) -> None:
        self.controller.go_to_pose(position=self.HOME_POSITION, orientation=self.HOME_ORIENTATION, duration=2.0)

    def step(self) -> Tuple[PandaState, Union[None, Exception]]:
        if rospy.is_shutdown():
            return None, Exception("rospy has shutdown")

        configuration = self.controller.get_configuration()
        position, orientation = self.controller.get_end_effector_pose()
        gripper = self.controller.get_gripper_width()

        self.rate.sleep()

        return PandaState(
            end_effector_position=position,
            end_effector_orientation=orientation,
            configuration=configuration,
            gripper_width=gripper,
        ), None

    def close(self) -> None:
        rospy.signal_shutdown("keyboard interrupt")
