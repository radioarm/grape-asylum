from dataclasses import dataclass, field
from xml.etree import ElementTree as et

@dataclass
class GrapeInfo:
    name: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    bbch: str = ''
    rotation: float = 0.0

    @property
    def is_rotated(self):
        return self.rotation > 0

    @property
    def rectangle(self):
        '''coordinates of points of corners of bounding box rectangle.
        '''
        return [
            [self.x_min, self.y_min], # top left
            [self.x_max, self.y_min], # top right
            [self.x_max, self.y_max], # bottom righ
            [self.x_min, self.y_max], # bottom left
        ]


@dataclass
class GrapesPhotoRepr:
    source_file: str
    img_filename: str
    grapes: list[GrapeInfo] = field(default_factory=list, repr=False)


def get_grape_attribute(grape_object: et.Element, attribute_name: str) -> str:
    try:
        return grape_object.find(f'.//attribute[name="{attribute_name}"]/value').text
    except AttributeError:
        return None


def extract_grape_info(grape_object: et.Element) -> list:
    bbch = get_grape_attribute(grape_object, 'BBCH')
    rotation = get_grape_attribute(grape_object, 'rotation')
    if rotation is not None:
        rotation = float(rotation)
    return [
        grape_object.find('./name').text,
        float(grape_object.find('.//xmin').text),
        float(grape_object.find('.//ymin').text),
        float(grape_object.find('.//xmax').text),
        float(grape_object.find('.//ymax').text),
        bbch,
        rotation
    ]


def get_grape_info_from_voc_tree(grape_data_tree: et.Element) -> list[GrapeInfo]:
    return [
        GrapeInfo(*extract_grape_info(grape_obj))
        for grape_obj in grape_data_tree.findall('object')
    ]


def get_grape_photo_reprs(fileset) -> list[GrapesPhotoRepr]:
    result = []
    for xml_file in fileset:
        tree = et.parse(xml_file).getroot()
        img_filename = tree.find('./filename').text.split('/')[0]
        if grapes := get_grape_info_from_voc_tree(tree):
            result.append(
                GrapesPhotoRepr(xml_file, img_filename, grapes)
            )
    return result


    # out = get_grape_photo_reprs(files)
    # grapes_num = sum(len(elem.grapes) for elem in out)

    # print(f'Number of files: {len(files)}')
    # print(f'Number of files with grapes: {len(out)}')
    # print(f'Number of grape obj: {grapes_num}')