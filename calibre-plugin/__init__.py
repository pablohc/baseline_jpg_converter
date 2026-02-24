#!/usr/bin/env python
# -*- coding: utf-8 -*-

from calibre.customize import InterfaceActionBase

class BaselineJPGConverterPlugin(InterfaceActionBase):
    name = 'Baseline JPEG Converter'
    description = 'Converts EPUB images to baseline JPEG (max 480x800) and fixes SVG-wrapped images for Crosspoint Reader compatibility'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Megabit'
    version = (2, 0, 0)
    minimum_calibre_version = (5, 0, 0)

    actual_plugin = 'ui:BaselineJPGAction'

    def is_customizable(self):
        return False
