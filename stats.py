# -*- coding: utf-8 -*-# -*- coding: utf-8 -*-

import hydra
import json
import omegaconf
import collections

from xml.etree import ElementTree as et

from utils import get_files_in_dir


def count_bbch_classes(xml_files: list[str]) -> dict[str, int]:

    stats = {}

    for xml_file in xml_files:
        # parse a given xml file and create subtree represenations
        xml_doc = et.parse(xml_file)
        root = xml_doc.getroot()

        # find all boundboxes and get their name
        for obj in root.findall('object'):
            object_name = obj.find('name').text

            if object_name not in stats:
                stats[object_name] = 1
            else:
                stats[object_name] += 1

    return stats


@hydra.main(version_base=None, config_path='conf', config_name='config')
def run(cfg: omegaconf.DictConfig) -> None:
    stats = count_bbch_classes(
        get_files_in_dir(dir_name=cfg.stats.xml_directory_path, extension='xml')
    )
    od = collections.OrderedDict(sorted(stats.items()))
    print(json.dumps(od, indent=4))

if __name__ == "__main__":
    run()