# -*- coding: utf-8 -*-

import abc
import contextlib
import hydra
import omegaconf
import os
import shutil
import uuid

from alive_progress import alive_bar
from xml.etree import ElementTree as et

from utils import get_files_in_dir


class AbstractVOCProcessStrategy(abc.ABC):
    ''' Abstract VOC file process strategy '''
    @abc.abstractmethod
    def apply(self, subtree: et.Element) -> et.Element:
        pass


class MoveBBCHCodeStrategy(AbstractVOCProcessStrategy):
    '''
        A strategy for extracting BBCH from attribute section
        of the XML file and place in the name tag
    '''
    def apply(self, grape_data_tree: et.Element) -> et.Element:
        for grape_object in grape_data_tree.findall('object'):
            bbch = grape_object.find('.//attribute[name="BBCH"]/value').text
            grape_object.find('./name').text = bbch
        return grape_data_tree


class RemoveRotatedGrapesStrategy(AbstractVOCProcessStrategy):
    '''
        A strategy for removing object subtree if the rotation is applied
    '''
    def apply(self, grape_data_tree: et.Element) -> et.Element:
        for grape_object in grape_data_tree.findall('object'):
            with contextlib.suppress(AttributeError):
                rotation_raw = grape_object.find(
                    './/attribute[name="rotation"]/value'
                ).text
                if float(rotation_raw) != 0:
                    grape_data_tree.remove(grape_object)
        return grape_data_tree


class RemoveUnwantedBBCHAnnotationsStrategy(AbstractVOCProcessStrategy):
    '''
        A strategy for removing object subtree if the BBCH code is not in the given list
    '''

    def __init__(self, bbch_codes: list[str]):
        self.bbch_codes = bbch_codes

    def apply(self, grape_data_tree: et.Element) -> et.Element:
        for grape_object in grape_data_tree.findall('object'):
            name_element = int(grape_object.find('./name').text)
            if name_element not in self.bbch_codes:
                grape_data_tree.remove(grape_object)
        return grape_data_tree


class ClusterBBCHCodeStrategy(AbstractVOCProcessStrategy):
    def __init__(self, bbch_code_clusters: list[list[int]]):
        self.bbch_code_clusters = {}
        for cluster in bbch_code_clusters:
            cluster_str_repr = '_'.join([str(elem) for elem in cluster])
            for elem in cluster:
                self.bbch_code_clusters[str(elem)] = cluster_str_repr

    def apply(self, grape_data_tree: et.Element) -> et.Element:
        for grape_object in grape_data_tree.findall('object'):
            name_element = grape_object.find('./name')
            if name_element.text not in self.bbch_code_clusters:
                grape_data_tree.remove(grape_object)
            else:
                name_element.text = self.bbch_code_clusters[name_element.text]
        return grape_data_tree


class GeneralizeBBCHCodeStrategy(AbstractVOCProcessStrategy):
    '''
        A strategy for casting specific BBCH code
        for their more general category accordin to

        https://en.wikipedia.org/wiki/BBCH-scale

    '''
    def apply(self, grape_data_tree: et.Element) -> et.Element:
        for grape_object in grape_data_tree.findall('object'):
            name_element = grape_object.find('./name')
            name_element.text = name_element.text[0]
        return grape_data_tree


class VOCProcessor:
    '''
    A VOC XML tree processor, accepts a list of strategies during initialization
    and subsequently applies them to the given subtree
    '''

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

            # parse a given xml file and create subtree represenations
            xml_doc = et.parse(xml_file)
            root = xml_doc.getroot()

            # apply transformation strategies
            voc_processor.process(root)

            if subtree_has_grapes(root):
                # if any grape bunch remains rename the file with random uuid
                # and place it in the targer directory

                img_filename = get_grape_img_filename(root)
                img_extension = img_filename.split('.')[-1]
                origin_img_file_path = f'{origin_img_files_path}{img_filename}'

                filename = uuid.uuid4()
                target_xml_filename = f'{filename}.xml'
                target_img_filename = f'{filename}.{img_extension}'

                target_img_filepath = f'{output_photos_path}{target_img_filename}'
                target_xml_filepath = f'{output_annotation_path}{target_xml_filename}'

                # remove folder name from xml tree
                root.find('./folder').text = ''
                # update img filename in the xml tree
                root.find('./filename').text = target_img_filename

                xml_doc.write(target_xml_filepath)
                shutil.copy(origin_img_file_path, target_img_filepath)

            progress_bar()


@hydra.main(version_base=None, config_path='conf', config_name='config')
def run(cfg: omegaconf.DictConfig) -> None:

    os.makedirs(cfg.data.output_annotation, exist_ok=True)
    os.makedirs(cfg.data.output_photos, exist_ok=True)

    voc_processor = VOCProcessor(
        strategies=[
            MoveBBCHCodeStrategy(),
            RemoveRotatedGrapesStrategy(),
            # RemoveUnwantedBBCHAnnotationsStrategy(cfg.data.required_bbch_codes)
            ClusterBBCHCodeStrategy(cfg.data.bbch_code_clusters)
            # GeneralizeBBCHCodeStrategy(),
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
