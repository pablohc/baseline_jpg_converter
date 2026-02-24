#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to create a ZIP file ready for Calibre plugin installation.
Run this script from the repository root, then install the generated .zip in Calibre.
"""

import zipfile
import shutil
import tempfile
import os
from pathlib import Path


def create_plugin_zip():
    """Create a ZIP file containing the Calibre plugin files."""

    # Create a temporary directory for the plugin structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Files go directly into the root of the ZIP (not in a subfolder)
        plugin_dir = Path(temp_dir)

        # Copy shared module to plugin (as shared/__init__.py and shared/converter.py)
        shared_src = Path(__file__).parent / 'shared'
        shared_dst = plugin_dir / 'shared'
        shutil.copytree(shared_src, shared_dst)

        # Copy plugin files to root
        calibre_src = Path(__file__).parent / 'calibre-plugin'
        shutil.copy(calibre_src / '__init__.py', plugin_dir / '__init__.py')
        shutil.copy(calibre_src / 'ui.py', plugin_dir / 'ui.py')

        # Copy about.txt if it exists
        about_src = Path(__file__).parent / 'about.txt'
        if about_src.exists():
            shutil.copy(about_src, plugin_dir / 'about.txt')

        # Create ZIP file - files should be at root level
        zip_name = 'baseline_jpg_converter.zip'

        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(plugin_dir.rglob('*')):
                if file.is_file():
                    # Use relative path from temp_dir (so files are at root of ZIP)
                    arcname = file.relative_to(plugin_dir)
                    zf.write(file, arcname)
                    print(f"Added: {arcname}")

    print(f"\nPlugin ZIP created: {zip_name}")
    print("\nTo install in Calibre:")
    print("1. Open Calibre")
    print("2. Go to Preferences → Advanced → Plugins")
    print("3. Click 'Load plugin from file'")
    print(f"4. Select {zip_name}")
    print("5. Restart Calibre")


if __name__ == '__main__':
    create_plugin_zip()
