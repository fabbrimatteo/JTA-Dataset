from typing import *

import cv2
import numpy as np

from joint import Joint


class Pose(list):
	LIMBS = [
		(0, 1),  # head_top -> head_center
		(1, 2),  # head_center -> neck
		(2, 3),  # neck -> right_clavicle
		(3, 4),  # right_clavicle -> right_shoulder
		(4, 5),  # right_shoulder -> right_elbow
		(5, 6),  # right_elbow -> right_wrist
		(2, 7),  # neck -> left_clavicle
		(7, 8),  # left_clavicle -> left_shoulder
		(8, 9),  # left_shoulder -> left_elbow
		(9, 10),  # left_elbow -> left_wrist
		(2, 11),  # neck -> spine0
		(11, 12),  # spine0 -> spine1
		(12, 13),  # spine1 -> spine2
		(13, 14),  # spine2 -> spine3
		(14, 15),  # spine3 -> spine4
		(15, 16),  # spine4 -> right_hip
		(16, 17),  # right_hip -> right_knee
		(17, 18),  # right_knee -> right_ankle
		(15, 19),  # spine4 -> left_hip
		(19, 20),  # left_hip -> left_knee
		(20, 21)  # left_knee -> left_ankle
	]


	def __init__(self, joints):
		# type: (List[Joint]) -> Pose
		super().__init__(joints)


	@property
	def invisible(self):
		# type: () -> bool
		"""
		:return: True if all the joints of the pose are occluded, False otherwise
		"""
		for j in self:
			if not j.occ:
				return False
		return True


	def draw(self, image, color):
		# type: (np.ndarray, List[int]) -> np.ndarray
		"""
		:param image: image on which to draw the pose
		:param color: color of the limbs make up the pose
		:return: image with the pose
		"""
		# draw limb(s) segments
		for (j_id_a, j_id_b) in Pose.LIMBS:
			joint_a = self[j_id_a] # type: Joint
			joint_b = self[j_id_b] # type: Joint
			t = 1 if joint_a.cam_distance > 25 else 2
			if joint_a.is_on_screen and joint_b.is_on_screen:
				cv2.line(image, joint_a.pos2d, joint_b.pos2d, color=color, thickness=t)

		# draw joint(s) circles
		for joint in self:
			image = joint.draw(image)

		return image
