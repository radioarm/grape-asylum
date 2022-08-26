# -*- coding: utf-8 -*-

import contextlib
import os
import typer
import uuid

from dataclasses import dataclass
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from rich.console import Console
from rich.progress import track
from xml.etree import ElementTree as et

from utils import get_files_in_dir


@dataclass
class GrapeBndBox:
    source_img_filename: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    bbch: str = ''

    @property
    def area(self):
        '''coordinates of points of corners of bounding box rectangle.
        '''
        return (self.x_min, self.y_min, self.x_max, self.y_max)


def process_annotations_dir(fileset: list[str]) -> tuple[list[GrapeBndBox], set[str]]:
    result = []
    bbch_codes = set()
    for xml_file in fileset:
        tree = et.parse(xml_file).getroot()
        img_filename = tree.find('./filename').text.split('/')[0]
        for grape_object in tree.findall('object'):
            with contextlib.suppress(AttributeError):
                bbch = grape_object.find('./name').text
                result.append(GrapeBndBox(
                    img_filename,
                    float(grape_object.find('.//xmin').text),
                    float(grape_object.find('.//ymin').text),
                    float(grape_object.find('.//xmax').text),
                    float(grape_object.find('.//ymax').text),
                    bbch
                ))
                bbch_codes.add(bbch)
    return result, bbch_codes


def crop_images(grapes: list[GrapeBndBox], photo_dir: str, output_dir:str) -> tuple[int, int]:
    success_counter = 0
    error_counter = 0
    for grape in track(grapes, description="Cropping..."):
        img_file = f'{photo_dir}/{grape.source_img_filename}'
        cropped_filename = f'{output_dir}/{grape.bbch}/{uuid.uuid4()}.jpg'
        try:
            img = Image.open(img_file)
            crop = img.crop(grape.area)
            crop.save(cropped_filename)
        except UnidentifiedImageError:
            error_counter +1
        else:
            success_counter += 1
    return success_counter, error_counter


def main(
    photos_dirname: Path = typer.Argument(
        ...,
        help="The directory with photos to crop",
        show_default=False,
        file_okay=False,
        dir_okay=True,
        exists=True
    ),
    annotations_dirname: Path = typer.Argument(
        ...,
        help="The directory with annotions (in PascalVOC format) containg bounding boxes",
        show_default=False,
        file_okay=False,
        dir_okay=True,
        exists=True
    ),
    output_directory: Path = typer.Argument(
        'output_cropped',
        help="The directory for output directories",
        file_okay=False,
        dir_okay=True,
        exists=False
    ),
) -> None:
    console = Console()
    with console.status('Processing annotations...'):
        grape_data, classes = process_annotations_dir(
            get_files_in_dir(dir_name=annotations_dirname, extension='xml'),
        )
    console.log(f"{len(grape_data)} grape bunches detected in {len(classes)} classes")

    console.log(f'Creating {len(classes)} class subdirs: {classes}')
    for class_name in classes:
        os.makedirs(f'{output_directory}/{class_name}', exist_ok=True)

    success_counter, error_counter = crop_images(grape_data, photos_dirname, output_directory)
    console.log('Cropping finished.')
    console.log(f'{success_counter} grape bunches cropped')
    console.log(f'{error_counter} img files not found')



if __name__ == "__main__":
    typer.run(main)