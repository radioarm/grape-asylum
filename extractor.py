# -*- coding: utf-8 -*-

import abc
import hydra
import uuid
import contextlib
import omegaconf
import os
import shutil

from alive_progress import alive_bar
from xml.etree import ElementTree as et

from utils import get_files_in_dir


class AbstractVOCProcessStrategy(abc.ABC):
    @abc.abstractmethod
    def apply(self, subtree: et.Element) -> et.Element:
        pass


class MoveBBCHCodeStrategy(AbstractVOCProcessStrategy):
    def apply(self, grape_data_tree: et.Element) -> et.Element:
        for grape_object in grape_data_tree.findall('object'):
            bbch = grape_object.find('.//attribute[name="BBCH"]/value').text
            grape_object.find('./name').text = bbch
        return grape_data_tree


class RemoveRotatedGrapesStrategy(AbstractVOCProcessStrategy):
    def apply(self, grape_data_tree: et.Element) -> et.Element:
        for grape_object in grape_data_tree.findall('object'):
            with contextlib.suppress(AttributeError):
                rotation_raw = grape_object.find(
                    './/attribute[name="rotation"]/value'
                ).text
                if float(rotation_raw) != 0:
                    grape_data_tree.remove(grape_object)
        return grape_data_tree


class VOCProcessor(abc.ABC):
    def __init__(self, strategies: list[AbstractVOCProcessStrategy]) -> None:
        self.strategies = strategies

    def process(self, subtree: et.Element) -> et.Element:
        for strategy in self.strategies:
            subtree = strategy.apply(subtree)
        return subtree


def subtree_has_grapes(grape_data_tree: et.Element) -> bool:
    return bool(grape_data_tree.findall('object'))


def get_raw_filename(full_filepath: str) -> str:
    return full_filepath.split('/')[-1]


def get_grape_img_filename(voc_tree: et.Element) -> str:
    return get_raw_filename(voc_tree.find('./filename').text)


def process_dataset(
    origin_voc_fileset: list[str],
    origin_img_files_path: str,
    voc_processor: VOCProcessor,
    output_annotation_path: str,
    output_photos_path: str,
) -> None:

    with alive_bar(
            len(origin_voc_fileset),
            dual_line=True,
            title='Processing images and VOC annotations') as progress_bar:

        for xml_file in origin_voc_fileset:
            progress_bar.text = f'Processing {xml_file}'

            xml_doc = et.parse(xml_file)
            root = xml_doc.getroot()

            voc_processor.process(root)

            if subtree_has_grapes(root):

                img_filename = get_grape_img_filename(root)
                img_extension = img_filename.split('.')[-1]
                origin_img_file_path = f'{origin_img_files_path}{img_filename}'

                filename = uuid.uuid4()
                target_img_filepath = f'{output_photos_path}{filename}.{img_extension}'
                target_xml_filepath = f'{output_annotation_path}{filename}.xml'

                xml_doc.write(target_xml_filepath)
                shutil.copy(origin_img_file_path, target_img_filepath)

            progress_bar()


@hydra.main(version_base=None, config_path='conf', config_name='config')
def run(cfg: omegaconf.DictConfig) -> None:
    with contextlib.suppress(FileExistsError):
        os.makedirs(cfg.data.output_annotation)
        os.makedirs(cfg.data.output_photos)

    voc_processor = VOCProcessor(
        strategies=[
            MoveBBCHCodeStrategy(),
            RemoveRotatedGrapesStrategy(),
        ]
    )

    process_dataset(
        get_files_in_dir(dir_name=cfg.data.annotations, extension='xml'),
        cfg.data.photos,
        voc_processor,
        cfg.data.output_annotation,
        cfg.data.output_photos,
    )


if __name__ == "__main__":
    run()
