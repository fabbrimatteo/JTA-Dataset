# -*- coding: utf-8 -*-

import numpy as np
from threading import Thread
import time
from path import Path
import json
from joint import Joint
from pose import Pose
import click
import sys

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


def create_data(anno: str, out_path: str, format: str):
    if not out_path.exists():
        out_path.makedirs()

    with open(anno, 'r') as json_file:
        matrix = json.load(json_file)

    matrix = np.array(matrix)

    # For the old style annotations
    # matrix[:, 6:8] = np.concatenate((-matrix[:, 7, None], matrix[:, 6, None]), axis=1)

    for frame_number in range(1, 901):
        if format == 'numpy':
            data_file_path = out_path / f'{frame_number}.npy'
        elif format == 'torch':
            data_file_path = out_path / f'{frame_number}.data'

        if not data_file_path.exists():
            frame_data = matrix[matrix[:, 0] == frame_number]

            poses = []
            for id in np.unique(frame_data[:, 1]):
                pose = get_pose(frame_data, id)
                if not pose.invisible:
                    poses.append(pose)

            if format == 'numpy':
                np.save(data_file_path, poses)
            elif format == 'torch':
                torch.save(poses, data_file_path)


class FrameDataCreatorThread(Thread):

    def __init__(self, anno: str, out_path: str, format: str):
        Thread.__init__(self)
        self.anno = anno
        self.out_path = out_path
        self.format = format


    def run(self):
        print('[{}] > START'.format(self.anno))
        create_data(self.anno, self.out_path, self.format)
        print('[{}] > DONE'.format(self.anno))


H1 = 'directory where you want to save the numpy annotations'
H2 = 'number of threads for multithreading'
H3 = 'the format to use to save the annotations (\'numpy\' or \'torch\'); DEFAULT = numpy'

@click.command()
@click.option('--out_dir_path', type=click.Path(), prompt='Enter \'out_dir_path\'', help=H1)
@click.option('--n_threads', type=int, default=4, help=H2)
@click.option('--format', type=click.Choice(['numpy', 'torch']), default='numpy', help=H3)
def main(out_dir_path, n_threads, format):
    # type: (str, int, str) -> None
    """
        Script that splits all the per sequence annotations into per frame annotations
         and saves them in a specified directory in numpy (or torch) format
    """
    if format == 'torch':
        global torch
        import torch

    start_time = time.time()

    for s in Path('annotations').dirs():

        annotations = s.files()

        for i in range(0, len(annotations), n_threads):
            threads = []
            for j in range(n_threads):
                out_subdir_path = out_dir_path / s.basename() / annotations[i + j].basename().split('.')[0]
                threads.append(FrameDataCreatorThread(annotations[i + j], out_subdir_path, format))

            for t in threads:
                t.start()

            for t in threads:
                t.join()

    print("\n\n===== DONE ===== [{:.2f} s]".format(time.time() - start_time))


if __name__ == "__main__":
    main()
