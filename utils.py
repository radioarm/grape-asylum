# -*- coding: utf-8 -*-

import os


def get_files_in_dir(*, dir_name, extension='') -> list[str]:
    if extension and not extension.startswith('.'):
        extension = f'.{extension}'
    return [
        os.path.join(dir_name, file) for file in os.listdir(dir_name)
        if file.endswith(extension)]
