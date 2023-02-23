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


MAX_COLORS = 42

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
def main(out_dir_path, max_frame):
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
