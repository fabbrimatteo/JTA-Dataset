# -*- coding: utf-8 -*-
# ---------------------

import json
import sys

import click
import imageio
import numpy as np
from path import Path

from joint import Joint
from pose import Pose

# Mapping used for the conversion from JTA to posetrack-keypoint format
index_mapping = [
    1,  # nose becomes head_center
    2,  # head_bottom becomes neck
    0,  # head_top is head_top
    7,  # left_ear becomes left_clavicle
    3,  # right_ear becomes right_clavicle
    8,  # left_shoulder is left_shoulder
    4,  # right_shoulder is right_shoulder
    9,  # left_elbow is left_elbow
    5,  # right_elbow is right_elbow
    10,  # left_wrist is left_wrist
    6,  # right_wrist is right_wrist
    19,  # left_hip is left_hip
    16,  # right_hip is right_hip
    20,  # left_knee is left_knee
    17,  # right_knee is right_knee
    21,  # left_ankle is left_ankle
    18,  # right_ankle is right_ankle
]

POSETRACK_SKELETON = [
    [16, 14],
    [14, 12],
    [17, 15],
    [15, 13],
    [12, 13],
    [6, 12],
    [7, 13],
    [6, 7],
    [6, 8],
    [7, 9],
    [8, 10],
    [9, 11],
    [2, 3],
    [1, 2],
    [1, 3],
    [2, 4],
    [3, 5],
    [4, 6],
    [5, 7]
]

# check python version
assert sys.version_info >= (3, 6), '[!] This script requires Python >= 3.6'


def get_pose(frame_data, person_id):
    # type: (np.ndarray, int) -> Pose
    """
    :param frame_data: data of the current frame
    :param person_id: person identifier
    :return: list of joints in the current frame with the required person ID
    """
    pose = [Joint(j) for j in frame_data[frame_data[:, 1] == person_id]]
    pose.sort(key=(lambda j: j.type))
    return Pose(pose, person_id)


H1 = 'path of the output directory'
H2 = 'Consider only the first n frames.' \
    + ' Must be a positive integer between 0 and 900.'


@click.command()
@click.option('--out_dir_path', type=click.Path(), prompt='Enter \'out_dir_path\'', help=H1)
@click.option('--max_frame', type=click.IntRange(min=0, max=900), prompt="Enter the number of frame to process" \
           + " (integer between 0 and 900)", help=H2)
@click.option('--use_posetrack_skeleton', is_flag=True, help='Use the PoseTrack skeleton')
def main(out_dir_path, max_frame, use_posetrack_skeleton):
    # type: (str) -> None
    """
    Script for annotation conversion (from JTA format to PoseTrack format)
    """

    out_dir_path = Path(out_dir_path).abspath()
    if not out_dir_path.exists():
        out_dir_path.makedirs()

    for dir in Path('annotations').dirs():
        basename = dir.basename()
        out_subdir_path = out_dir_path / basename
        if not out_subdir_path.exists():
            out_subdir_path.makedirs()
        print(f'▸ converting \'{basename}\' set')
        for anno in dir.files():

            with open(anno, 'r') as json_file:
                data = json.load(json_file)
                data = np.array(data)

            print(f'▸ converting annotations of \'{Path(anno).abspath()}\'')

            # getting sequence number from `anno`
            sequence = None
            try:
                sequence = int(Path(anno).basename().split('_')[1].split('.')[0])
            except:
                print('[!] error during conversion.')
                print('\ttry using JSON files with the original nomenclature.')

            if use_posetrack_skeleton:
                posetrack_dict = {
                    'images': [],
                    'annotations': [],
                    'categories': [{
                        'supercategory': 'person',
                        'id': 1,
                        'name': 'person',
                        'keypoints': [Joint.NAMES[index] for index in index_mapping],
                        'skeleton': POSETRACK_SKELETON
                    }]
                }
            else:
                posetrack_dict = {
                    'images': [],
                    'annotations': [],
                    'categories': [{
                        'supercategory': 'person',
                        'id': 1,
                        'name': 'person',
                        'keypoints': Joint.NAMES,
                        'skeleton': Pose.SKELETON
                    }]
                }

            for frame_number in range(0, max_frame):

                image_id = sequence * 1000 + (frame_number + 1)
                posetrack_dict['images'].append({
                    "has_no_densepose": True,
                    "is_labeled": True,
                    "file_name": f"frames/{basename}/seq_{sequence}/{frame_number + 1}.jpg",
                    "nframes": max_frame,
                    "frame_id": image_id,
                    "vid_id": f"{sequence}",
                    "id": image_id
                })

                # NOTE: frame #0 does NOT exists: first frame is #1
                frame_data = data[data[:, 0] == frame_number + 1]  # type: np.ndarray

                for p_id in set(frame_data[:, 1]):
                    pose = get_pose(frame_data=frame_data, person_id=p_id)

                    # ignore the "invisible" poses
                    # (invisible pose = pose of which I do not see any joint)
                    if pose.invisible:
                        continue

                    annotation = pose.posetrack_annotation
                    if use_posetrack_skeleton:
                        nested_keypoints = [annotation['keypoints'][3 * index:3 * (index+1)] for index in index_mapping]
                        annotation['keypoints'] = [item for keypoints in nested_keypoints for item in keypoints]
                    annotation['image_id'] = image_id
                    annotation['id'] = image_id * 100000 + int(p_id)
                    annotation['category_id'] = 1
                    annotation['scores'] = []
                    posetrack_dict['annotations'].append(annotation)

                print(f'\r▸ progress: {100 * (frame_number / (max_frame-1)):6.2f}%', end='')

            print()
            out_file_path = out_subdir_path / f'seq_{sequence}.json'
            with open(out_file_path, 'w') as f:
                json.dump(posetrack_dict, f)


if __name__ == '__main__':
    main()
