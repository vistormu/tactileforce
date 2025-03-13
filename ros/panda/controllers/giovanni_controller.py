from typing import Sequence, Tuple

import numpy as np
import rospy
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray

from .controller import Controller


class GiovanniController(Controller):
    def __init__(self) -> None:
        self.end_effector_position = np.zeros(3)
        self.end_effector_orientation = np.zeros(4)
        self.configuration = np.zeros(7)

    def start(self) -> None:
        # subscribers
        rospy.Subscriber("/cartesian_pose", PoseStamped, self._cartesian_pose_callback)
        rospy.Subscriber("/joint_states", JointState, self._joint_states_callback)

        # publishers
        self.configuration_pub = rospy.Publisher('/equilibrium_configuration', Float32MultiArray, queue_size=0)
        self.equilibrium_pose_pub = rospy.Publisher("/equilibrium_pose", PoseStamped, queue_size=0)

    def _cartesian_pose_callback(self, pose: PoseStamped) -> None:
        position = pose.pose.position
        orientation = pose.pose.orientation
        self.end_effector_position = np.array([position.x, position.y, position.z])
        self.end_effector_orientation = np.array([orientation.w, orientation.x, orientation.y, orientation.z])

    def _joint_states_callback(self, configuration: JointState) -> None:
        self.configuration = np.array(configuration.position[:7])

    def set_pose(self, position: Sequence[float], orientation: Sequence[float]) -> None:
        msg = PoseStamped()
        msg.pose.position.x = position[0]
        msg.pose.position.y = position[1]
        msg.pose.position.z = position[2]
        msg.pose.orientation.w = orientation[0]
        msg.pose.orientation.x = orientation[1]
        msg.pose.orientation.y = orientation[2]
        msg.pose.orientation.z = orientation[3]

        self.equilibrium_pose_pub.publish(msg)

    def go_to_pose(self, position: Sequence[float], orientation: Sequence[float], duration: float) -> None:
        # TODO: interpolate orientation

        distance_step = 0.001
        start = self.end_effector_position
        goal = np.array(position)

        total_distance = np.linalg.norm(goal - start)
        num_intervals = int(np.ceil(total_distance / distance_step))

        frequency = num_intervals / duration
        points = np.linspace(start, goal, num_intervals + 1)

        rate = rospy.Rate(frequency)
        for point in points:
            self.set_pose(point, orientation)
            rate.sleep()

    def get_configuration(self) -> np.ndarray:
        return self.configuration

    def get_end_effector_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        return self.end_effector_position, self.end_effector_orientation
