from typing import Sequence, Tuple

import numpy as np
import rospy
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32MultiArray
from franka_gripper.msg import GraspActionGoal
from dynamic_reconfigure.client import Client

from .controller import Controller


class GiovanniController(Controller):
    def __init__(self) -> None:
        self.end_effector_position = np.zeros(3)
        self.end_effector_orientation = np.zeros(4)
        self.configuration = np.zeros(7)
        self.gripper_width = 0

    def start(self) -> None:
        # subscribers
        rospy.Subscriber("/cartesian_pose", PoseStamped, self._cartesian_pose_callback)
        rospy.Subscriber("/joint_states", JointState, self._joint_states_callback)

        # publishers
        self.configuration_pub = rospy.Publisher('/equilibrium_configuration', Float32MultiArray, queue_size=0)
        self.equilibrium_pose_pub = rospy.Publisher("/equilibrium_pose", PoseStamped, queue_size=0)
        self.gripper_grasp_pub = rospy.Publisher("/franka_gripper/grasp/goal", GraspActionGoal, queue_size=0)

        # clients
        self.stiffness_client = Client("/dynamic_reconfigure_compliance_param_node", config_callback=None)

    def _cartesian_pose_callback(self, pose: PoseStamped) -> None:
        position = pose.pose.position
        orientation = pose.pose.orientation
        self.end_effector_position = np.array([position.x, position.y, position.z])
        self.end_effector_orientation = np.array([orientation.w, orientation.x, orientation.y, orientation.z])

    def _joint_states_callback(self, configuration: JointState) -> None:
        self.configuration = np.array(configuration.position[:7])
        self.gripper_width = configuration.position[7] + configuration.position[8]

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

    def grasp(self, width: float, speed: float, force: float) -> None:
        msg = GraspActionGoal()
        msg.goal.epsilon.inner = 0.3
        msg.goal.epsilon.outer = 0.3
        msg.goal.speed = speed
        msg.goal.force = force
        msg.goal.width = width

        self.gripper_grasp_pub.publish(msg)

    def get_gripper_width(self) -> float:
        return self.gripper_width

    def set_stiffness(self, translational: Sequence[float], rotational: Sequence[float], nullspace: float) -> None:
        self.stiffness_client.update_configuration({
            "translational_stiffness_X": translational[0],
            "translational_stiffness_Y": translational[1],
            "translational_stiffness_Z": translational[2],
            "rotational_stiffness_X": rotational[0],
            "rotational_stiffness_Y": rotational[1],
            "rotational_stiffness_Z": rotational[2],
            "nullspace_stiffness": nullspace,
        })
