# -*- coding: utf-8 -*-

import os
import typer
import random
import shutil

from alive_progress import alive_bar

from utils import get_files_in_dir


def extract_filename(filepath: str) -> str:
    return filepath.split('/')[-1]


def main(
    dirname: str = typer.Argument(
        ...,
        help="The directory with photos and annotations subdirs to split into 80/20 train/validation subsets",
        show_default=False,
    ),
    train_percentage: float = typer.Argument(
        0.8,
        help="The fracture of photos put into training subset",
    ),
) -> None:

    print('Setting things up...')

    # setup output directories
    target_train_photos_dir = f'{dirname}/split/train/photos/'
    target_train_annotations_dir = f'{dirname}/split/train/annotations/'
    target_validation_photos_dir = f'{dirname}/split/validate/photos/'
    target_validation_annotations_dir = f'{dirname}/split/validate/annotations/'

    os.makedirs(target_train_photos_dir, exist_ok=True)
    os.makedirs(target_train_annotations_dir, exist_ok=True)
    os.makedirs(target_validation_photos_dir, exist_ok=True)
    os.makedirs(target_validation_annotations_dir, exist_ok=True)

    # get source files
    source_photos_dir = os.path.join(dirname, 'photos')
    source_annotations_dir = os.path.join(dirname, 'annotations')
    image_files = get_files_in_dir(dir_name=source_photos_dir, extension='jpg')
    annotations_files = get_files_in_dir(
        dir_name=source_annotations_dir, extension='xml'
    )

    # sort file list to preserve filenames compatibility
    image_files.sort()
    annotations_files.sort()

    # count source files
    files_counter = len(image_files)
    train_count = int(train_percentage * files_counter)

    # split data into trainset and testset randomly
    file_pairs = list(zip(image_files, annotations_files))
    random.shuffle(file_pairs)

    training_set = file_pairs[:train_count]
    validation_set = file_pairs[train_count:]

    # move files to respective subdirs
    with alive_bar(
        train_count, dual_line=True, title='Copying training files'
    ) as progress_bar:
        for training_photo, training_annotation in training_set:
            shutil.copy(
                training_photo,
                target_train_photos_dir + extract_filename(training_photo),
            )
            shutil.copy(
                training_annotation,
                target_train_annotations_dir + extract_filename(training_annotation),
            )
            progress_bar()

    with alive_bar(
        files_counter - train_count, dual_line=True, title='Copying validation files'
    ) as progress_bar:
        for validation_photo, validation_annotation in validation_set:
            shutil.copy(
                validation_photo,
                target_validation_photos_dir + extract_filename(validation_photo),
            )
            shutil.copy(
                validation_annotation,
                target_validation_annotations_dir + extract_filename(validation_annotation),
            )
            progress_bar()

if __name__ == "__main__":
    typer.run(main)
