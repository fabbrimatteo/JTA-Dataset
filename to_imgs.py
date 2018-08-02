# -*- coding: utf-8 -*-
# ---------------------

import click
import imageio
from path import Path

imageio.plugins.ffmpeg.download()

H1 = 'path of the video from which you want to extract the frames'
H2 = 'directory where you want to save the extracted frames'
H3 = 'number from which to start counting the video frames; DEFAULT = 1'
H4 = 'the format to use to save the images/frames; DEFAULT = jpg'


@click.command()
@click.option('--in_mp4_file_path', type=click.Path(exists=True), prompt='Enter \'in_mp4_file_path\'', help=H1)
@click.option('--out_dir_path', type=click.Path(), prompt='Enter \'out_dir_path\'', help=H2)
@click.option('--first_frame', type=int, default=1, help=H3)
@click.option('--img_format', type=str, default='jpg', help=H4)
def main(in_mp4_file_path, out_dir_path, first_frame, img_format):
	# type: (str, str, int, str) -> None
	"""
	Script that, given a video, splits it into its frames and saves them
	in a specified directory with the desired format
	"""
	out_dir_path = Path(out_dir_path)
	if not out_dir_path.exists():
		out_dir_path.makedirs()
	reader = imageio.get_reader(in_mp4_file_path)

	print(f'▸ extracting frames of \'{Path(in_mp4_file_path).abspath()}\'')
	for frame_number, image in enumerate(reader):
		n = first_frame + frame_number
		imageio.imwrite(out_dir_path/f'{n}.{img_format}', image)
		print(f'\r▸ progress: {100*(frame_number/899):6.2f}%', end='')
	print(f'\n▸ direcory with extracted frames: \'{out_dir_path.abspath()}\'\n')


if __name__ == '__main__':
	main()
