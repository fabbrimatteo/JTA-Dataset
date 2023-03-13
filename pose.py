# -*- coding: utf-8 -*-
# ---------------------

from typing import *

import cv2
import numpy as np

from joint import Joint


class Pose(list):
    """
	a Pose is a list of Joint(s) belonging to the same person.
	"""

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

    SKELETON = [[l[0] + 1, l[1] + 1] for l in LIMBS]

    def __init__(self, joints, person_id=None):
        # type: (List[Joint]) -> None
        super().__init__(joints)
        self.person_id = int(person_id)

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

    @property
    def bbox_2d(self):
        # type: () -> List[int]
        """
		:return: bounding box around the pose in format [x_min, y_min, width, height]
			- x_min = x of the top left corner of the bounding box
			- y_min = y of the top left corner of the bounding box
		"""
        x_min = int(np.min([j.x2d for j in self]))
        y_min = int(np.min([j.y2d for j in self]))
        x_max = int(np.max([j.x2d for j in self]))
        y_max = int(np.max([j.y2d for j in self]))
        width = x_max - x_min
        height = y_max - y_min
        return [x_min, y_min, width, height]

    @property
    def bbox_head_2d(self):
        # type: () -> List[int]
        """
		The bbox_head is computed by tacking a square centered around the head with
		sides of length equal to two times the distance between the head_top and head_center.
        WARNING: it may be wrong !
        :return: bounding box around the head in format [x_min, y_min, width, height]
            - x_min = x of the top left corner of the head bounding box
            - y_min = y of the top left corner of the head bounding box
        """
        bbox_length = 2 * np.sqrt((self[0].x2d - self[1].x2d) ** 2 + (self[0].y2d - self[1].y2d) ** 2)
        x_min = int(self[1].x2d - bbox_length / 2)
        y_min = int(self[1].y2d - bbox_length / 2)
        width = int(bbox_length)
        height = int(bbox_length)
        return [x_min, y_min, width, height]

    @property
    def bbox_2d_padded(self, h_inc_perc=0.15, w_inc_perc=0.1):
        x_min = int(np.min([j.x2d for j in self]))
        y_min = int(np.min([j.y2d for j in self]))
        x_max = int(np.max([j.x2d for j in self]))
        y_max = int(np.max([j.y2d for j in self]))
        width = x_max - x_min
        height = y_max - y_min

        inc_h = (height * h_inc_perc) / 2
        inc_w = (width * w_inc_perc) / 2

        x_min = x_min - inc_w
        x_max = x_max + inc_w

        y_min = y_min - inc_h
        y_max = y_max + inc_h

        width = x_max - x_min
        height = y_max - y_min

        return [x_min, y_min, width, height]

    @property
    def coco_annotation(self):
        # type: () -> Dict
        """
		:return: COCO annotation dictionary of the pose
		==========================================================
		NOTE#1: in COCO, each keypoint is represented by its (x,y)
		2D location and a visibility flag `v` defined as:
			- `v=0` ==> not labeled (in which case x=y=0)
			- `v=1` ==> labeled but not visible
			- `v=2` ==> labeled and visible
		==========================================================
		NOTE#2: in COCO, a keypoint is considered visible if it
		falls inside the object segment. In JTA there are no
		object segments and every keypoint is labelled, so we
		v=2 for each keypoint.
		==========================================================
		"""
        keypoints = []
        for j in self:
            keypoints += [j.x2d, j.y2d, 2]
        annotation = {
            'keypoints': keypoints,
            'num_keypoints': len(self),
            'bbox': self.bbox_2d
        }
        return annotation

    @property
    def posetrack_annotation(self):
        # type: () -> Dict
        """
        :return: PoseTrack annotation dictionary of the pose
        ==========================================================
        NOTE#1: in PoseTrack, each keypoint is represented by its (x,y)
        2D location and a visibility flag `v` defined as:
            - `v=0` ==> not visible
            - `v=1` ==> visible
        ==========================================================
        NOTE#2: in PoseTrack, keypoints that are not visible are not labeled and
        set to (x=y=v=0). In JTA every keypoint is labelled, so keypoints with
        v = 0 are labelled with their true (x,y) location.
        ==========================================================
        NOTE#3: in PoseTrack, the bbox_head attribute has been human annotated.
        The bbox_head is computed by tacking a square centered around the head with
        sides of length equal to two times the distance between the head_top and
        head_center.
        WARNING: it may be wrong !
        ==========================================================
        """
        keypoints = []
        for j in self:
            if j.occ:
                keypoints += [j.x2d, j.y2d, 0]
            else:
                keypoints += [j.x2d, j.y2d, 1]
        annotation = {
            'bbox_head': self.bbox_head_2d,
            'keypoints': keypoints,
            'bbox': self.bbox_2d,
            'track_id': self.person_id,
        }
        return annotation

    def draw(self, image, color):
        # type: (np.ndarray, List[int]) -> np.ndarray
        """
		:param image: image on which to draw the pose
		:param color: color of the limbs make up the pose
		:return: image with the pose
		"""
        # draw limb(s) segments
        for (j_id_a, j_id_b) in Pose.LIMBS:
            joint_a = self[j_id_a]  # type: Joint
            joint_b = self[j_id_b]  # type: Joint
            t = 1 if joint_a.cam_distance > 25 else 2
            if joint_a.is_on_screen and joint_b.is_on_screen:
                cv2.line(image, joint_a.pos2d, joint_b.pos2d, color=color, thickness=t)

        # draw joint(s) circles
        for joint in self:
            image = joint.draw(image)

        return image

    def __iter__(self):
        # type: () -> Iterator[Joint]
        return super().__iter__()
