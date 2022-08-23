# -*- coding: utf-8 -*-

import hydra
import json
import omegaconf
import os

from xml.etree import ElementTree as et

from utils import get_files_in_dir


def transorm_voc_to_aws_json(input_xml_files: list[str], output_path: str) -> None:
    '''
    Transforms a list of Pascal VOC files into AWS json format and saves them in the given directory

        Parameters:
            input_xml_files: A list of xml file paths
            output_path: Output directory
    '''

    # dictonary for all classes found in the dataset
    # keys are bbch codes
    # values are subsequent integers created when adding new entries to this dictionary
    global_classes = {}

    for input_xml_file in input_xml_files:
        # parse xml tree
        xml_doc = et.parse(input_xml_file)
        root = xml_doc.getroot()

        # extract image metadata
        image_filename = root.find('filename').text
        image_width = int(root.find('size/width').text)
        image_height = int(root.find('size/height').text)

        # AWS json document template
        json_document = {
            'file': image_filename,
            'image_size': [
                {
                    'width': image_width,
                    'height': image_height,
                    'depth': 3
                }
            ],
            'annotations': [],
            'categories': [],
        }

        current_file_categories = {}

        for obj in root.findall('object'):

            object_name = obj.find('name').text
            # preserving class id and and class name consistency
            # between files from the dataset
            if object_name not in global_classes:
                global_classes[object_name] = len(global_classes)

            class_id = global_classes[object_name]
            current_file_categories[class_id] = object_name

            # find bound boxes
            xmin = float(obj.find('bndbox/xmin').text)
            ymin = float(obj.find('bndbox/ymin').text)
            xmax = float(obj.find('bndbox/xmax').text)
            ymax = float(obj.find('bndbox/ymax').text)

            # transoform xmin, xmax to bound box width
            width = round(xmax - xmin, 2)
            # transoform ymin, ymax to bound box height
            height = round(ymax - ymin, 2)

            json_document['annotations'].append({
                'class_id': class_id,
                'top': ymin,
                'left': xmin,
                'width': width,
                'height': height,
            })

        json_document['categories'] = [
            {'class_id': class_id, 'name': name}
            for class_id, name in current_file_categories.items()
        ]

        # serialize json_document into json format
        # and save it to the file in the given directory
        json_filename = input_xml_file.split('/')[-1].replace('xml', 'json')
        with open(os.path.join(output_path, json_filename), 'w') as json_file:
            json.dump(json_document, json_file, indent=2)


@hydra.main(version_base=None, config_path='conf', config_name='config')
def run(cfg: omegaconf.DictConfig) -> None:

    os.makedirs(cfg.voc_transformer.target_annotation_path, exist_ok=True)

    transorm_voc_to_aws_json(
        input_xml_files=get_files_in_dir(
            dir_name=cfg.voc_transformer.source_annotations_path, extension='xml'),
        output_path=cfg.voc_transformer.target_annotation_path,
    )


if __name__ == "__main__":
    run()
