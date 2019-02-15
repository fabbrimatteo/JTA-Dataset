# -*- coding: utf-8 -*-
# ---------------------

import sys

import click
import imageio
from path import Path


imageio.plugins.ffmpeg.download()

H1 = 'directory where you want to save the extracted frames'
H2 = 'number from which to start counting the video frames; DEFAULT = 1'
H3 = 'the format to use to save the images/frames; DEFAULT = jpg'

# check python version
assert sys.version_info >= (3, 6), '[!] This script requires Python >= 3.6'


@click.command()
@click.option('--out_dir_path', type=click.Path(), prompt='Enter \'out_dir_path\'', help=H1)
@click.option('--first_frame', type=int, default=1, help=H2)
@click.option('--img_format', type=str, default='jpg', help=H3)
def main(out_dir_path, first_frame, img_format):
    # type: (str, int, str) -> None
    """
    Script that splits all the videos into frames and saves them
    in a specified directory with the desired format
    """
    out_dir_path = Path(out_dir_path)
    if not out_dir_path.exists():
        out_dir_path.makedirs()

    for dir in Path('videos').dirs():
        out_subdir_path = out_dir_path / dir.basename()
        if not out_subdir_path.exists():
            out_subdir_path.makedirs()
        print(f'▸ extracting \'{dir.basename()}\' set')
        for video in dir.files():
            out_seq_path = out_subdir_path / video.basename().split('.')[0]
            if not out_seq_path.exists():
                out_seq_path.makedirs()
            reader = imageio.get_reader(video)
            print(f'▸ extracting frames of \'{Path(video).abspath()}\'')
            for frame_number, image in enumerate(reader):
                n = first_frame + frame_number
                imageio.imwrite(out_seq_path / f'{n}.{img_format}', image)
                print(f'\r▸ progress: {100 * (frame_number / 899):6.2f}%', end='')
            print()


if __name__ == '__main__':
    main()
