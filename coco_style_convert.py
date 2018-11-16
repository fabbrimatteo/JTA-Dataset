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

imageio.plugins.ffmpeg.download()
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
	return Pose(pose)


H1 = 'path of JSON annotation file (JTA format)'
H2 = 'path of the output directory'


@click.command()
@click.option('--json_file_path', type=click.Path(exists=True), prompt='Enter \'json_file_path\'', help=H1)
@click.option('--out_dir_path', type=click.Path(), prompt='Enter \'out_dir_path\'', help=H2)
def main(json_file_path, out_dir_path):
	# type: (str, str) -> None
	"""
	Script that provides a visual representation of the annotations
	"""

	print(f'▸ converting annotations of \'{Path(json_file_path).abspath()}\'')

	out_dir_path = Path(out_dir_path).abspath()
	if not out_dir_path.exists():
		out_dir_path.makedirs()

	with open(json_file_path, 'r') as json_file:
		data = json.load(json_file)
		data = np.array(data)

	# getting sequence number from `json_file_path`
	sequence = None
	try:
		sequence = int(Path(json_file_path).basename().split('_')[1].split('.')[0])
	except:
		print('[!] error during conversion.')
		print('\ttry using JSON files with the original nomenclature.')

	coco_dict = {
		'info': {
			'description': f'JTA 2018 Dataset - Sequence #{sequence}',
			'url': 'http://aimagelab.ing.unimore.it/jta',
			'version': '1.0',
			'year': 2018,
			'contributor': 'AImage Lab',
			'date_created': '2018/01/28',
		},
		'licences': [{
			'url': 'http://creativecommons.org/licenses/by-nc/2.0',
			'id': 2,
			'name': 'Attribution-NonCommercial License'
		}],
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

	for frame_number in range(0, 900):

		image_id = sequence*1000 + (frame_number + 1)
		coco_dict['images'].append({
			'license': 4,
			'file_name': f'{frame_number + 1}.jpg',
			'height': 1080,
			'width': 1920,
			'date_captured': '2018-01-28 00:00:00',
			'id': image_id
		})

		# NOTE: frame #0 does NOT exists: first frame is #1
		frame_data = data[data[:, 0] == frame_number + 1]  # type: np.ndarray

		for p_id in set(frame_data[:, 1]):
			pose = get_pose(frame_data=frame_data, person_id=p_id)

			# ignore the "invisible" poses
			# (invisible pose = pose of which I do not see any joint)
			if pose.invisible:
				continue

			annotation = pose.coco_annotation
			annotation['image_id'] = image_id
			annotation['id'] = image_id*100000 + int(p_id)
			annotation['category_id'] = 1
			coco_dict['annotations'].append(annotation)

		print(f'\r▸ progress: {100*(frame_number/899):6.2f}%', end='')

	out_file_path = out_dir_path/f'seq_{sequence}.coco.json'
	with open(out_file_path, 'w') as f:
		json.dump(coco_dict, f)
	print(f'\r▸ converted file: \'{out_file_path.abspath()}\'')


if __name__ == '__main__':
	main()
