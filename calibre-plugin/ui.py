#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Calibre plugin UI for Baseline JPEG Converter.
Uses shared conversion logic from ../shared/converter.py
"""

import sys
import os
from pathlib import Path

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog
from qt.core import QProgressDialog, Qt

# Add parent directory to path to import shared module
plugin_dir = Path(__file__).parent.parent
if str(plugin_dir) not in sys.path:
    sys.path.insert(0, str(plugin_dir))

from shared.converter import EpubConverterShared


class BaselineJPGAction(InterfaceAction):
    name = 'Baseline JPEG Converter'
    action_spec = ('Baseline JPEG Converter', None, 'Convert images to baseline JPEG (max 480x800), and fix SVG-wrapped images', None)
    action_type = 'current'

    def genesis(self):
        self.qaction.triggered.connect(self.convert_covers)
        self.converter = EpubConverterShared()

    def convert_covers(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            error_dialog(self.gui, 'No Selection',
                        'Please select one or more books first.', show=True)
            return

        book_ids = list(map(self.gui.library_view.model().id, rows))
        self.do_convert(book_ids)

    def convert_epub_images(self, epub_path):
        """Convert EPUB images using shared logic."""
        import tempfile
        import shutil

        converted_count = 0
        svg_images_fixed = 0
        cover_meta_added = False
        renamed_files = {}

        temp_fd, temp_path = tempfile.mkstemp(suffix='.epub')
        os.close(temp_fd)

        try:
            import zipfile
            import re

            with zipfile.ZipFile(epub_path, 'r') as zin:
                # First pass: identify files to rename
                for item in zin.infolist():
                    if item.is_dir():
                        continue
                    lower_name = item.filename.lower()
                    if lower_name.endswith(('.png', '.gif', '.webp', '.bmp')):
                        base_name = item.filename.rsplit('.', 1)[0]
                        new_name = base_name + '.jpg'
                        renamed_files[item.filename] = new_name

                # Second pass: process and write files
                with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        if item.is_dir():
                            continue
                        data = zin.read(item.filename)
                        filename = item.filename
                        lower_name = filename.lower()

                        # Convert images to baseline JPEG
                        if lower_name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')):
                            new_data = self.converter.convert_image_to_baseline(data)
                            if new_data:
                                data = new_data
                                converted_count += 1
                                if filename in renamed_files:
                                    filename = renamed_files[filename]

                        # Fix SVG images in HTML/XHTML files
                        elif lower_name.endswith(('.xhtml', '.html', '.htm')):
                            try:
                                text = data.decode('utf-8')
                                text, fixed_count = self.converter.fix_svg_images(text, filename)
                                svg_images_fixed += fixed_count

                                # Update image references for renamed files
                                for old_name, new_name in renamed_files.items():
                                    old_basename = old_name.split('/')[-1]
                                    new_basename = new_name.split('/')[-1]
                                    text = text.replace(old_basename, new_basename)
                                    text = text.replace(old_name, new_name)
                                data = text.encode('utf-8')
                            except Exception:
                                pass

                        # Update CSS files
                        elif lower_name.endswith('.css'):
                            try:
                                text = data.decode('utf-8')
                                for old_name, new_name in renamed_files.items():
                                    old_basename = old_name.split('/')[-1]
                                    new_basename = new_name.split('/')[-1]
                                    text = text.replace(old_basename, new_basename)
                                    text = text.replace(old_name, new_name)
                                data = text.encode('utf-8')
                            except Exception:
                                pass

                        # Update NCX files
                        elif lower_name.endswith('.ncx'):
                            try:
                                text = data.decode('utf-8')
                                for old_name, new_name in renamed_files.items():
                                    old_basename = old_name.split('/')[-1]
                                    new_basename = new_name.split('/')[-1]
                                    text = text.replace(old_basename, new_basename)
                                    text = text.replace(old_name, new_name)
                                data = text.encode('utf-8')
                            except Exception:
                                pass

                        # Update OPF files
                        elif lower_name.endswith('.opf'):
                            try:
                                text = data.decode('utf-8')

                                # Update image references
                                for old_name, new_name in renamed_files.items():
                                    old_basename = old_name.split('/')[-1]
                                    new_basename = new_name.split('/')[-1]
                                    text = text.replace(old_basename, new_basename)
                                    text = text.replace(old_name, new_name)

                                # Fix media-types for renamed images
                                text = re.sub(
                                    r'href="([^"]+\.jpg)"([^>]*)media-type="image/(png|gif|webp|bmp)"',
                                    r'href="\1"\2media-type="image/jpeg"',
                                    text
                                )
                                text = re.sub(
                                    r'media-type="image/(png|gif|webp|bmp)"([^>]*)href="([^"]+\.jpg)"',
                                    r'media-type="image/jpeg"\2href="\3"',
                                    text
                                )

                                # Remove svg from properties if we fixed any images
                                if svg_images_fixed > 0:
                                    text = re.sub(r'\s+svg(?=["\s>])', '', text)
                                    text = text.replace('properties=" "', '')
                                    text = text.replace("properties=' '", '')

                                # Ensure cover meta exists
                                text, meta_added = self.converter.ensure_cover_meta(text)
                                if meta_added:
                                    cover_meta_added = True

                                data = text.encode('utf-8')
                            except Exception:
                                pass

                        # Write file to new EPUB
                        if item.filename == 'mimetype':
                            zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
                        else:
                            new_info = zipfile.ZipInfo(filename)
                            new_info.compress_type = zipfile.ZIP_DEFLATED
                            zout.writestr(new_info, data)

            # Generate output filename with .x4.epub extension
            output_path = epub_path.replace('.epub', '.x4.epub')
            if output_path == epub_path:
                output_path = epub_path + '.x4.epub'
            shutil.move(temp_path, output_path)

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

        return converted_count, svg_images_fixed, cover_meta_added

    def do_convert(self, book_ids):
        from PIL import Image
        from io import BytesIO

        db = self.gui.current_db.new_api
        converted_covers = 0
        converted_epub_images = 0
        svg_images_fixed = 0
        cover_metas_added = 0
        errors = []

        progress = QProgressDialog('Converting images...', 'Cancel', 0, len(book_ids), self.gui)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle('Converting to Baseline JPEG')

        for i, book_id in enumerate(book_ids):
            if progress.wasCanceled():
                break

            progress.setValue(i)
            title = db.field_for('title', book_id)
            progress.setLabelText(f'Processing: {title}\n({i+1} of {len(book_ids)})')

            try:
                cover_data = db.cover(book_id)
                if cover_data:
                    new_data = self.converter.convert_image_to_baseline(cover_data)
                    if new_data:
                        db.set_cover({book_id: new_data})
                        converted_covers += 1
            except Exception as e:
                errors.append(f'{title} (cover): {str(e)}')

            try:
                formats = db.formats(book_id)
                if formats and 'EPUB' in formats:
                    epub_path = db.format_abspath(book_id, 'EPUB')
                    if epub_path and os.path.exists(epub_path):
                        # Convert EPUB - creates a new .x4.epub file alongside the original
                        img_count, svg_count, meta_added = self.convert_epub_images(epub_path)
                        converted_epub_images += img_count
                        svg_images_fixed += svg_count
                        if meta_added:
                            cover_metas_added += 1
            except Exception as e:
                errors.append(f'{title} (EPUB): {str(e)}')

        progress.setValue(len(book_ids))

        msg = f'Converted {converted_covers} cover(s) and {converted_epub_images} EPUB image(s) to baseline JPEG.'
        if svg_images_fixed > 0:
            msg += f'\nFixed {svg_images_fixed} SVG-wrapped image(s).'
        if cover_metas_added > 0:
            msg += f'\nAdded {cover_metas_added} cover meta tag(s).'
        if converted_epub_images > 0 or svg_images_fixed > 0:
            msg += f'\n\n.x4.epub files created in your Calibre library folder.'

        if errors:
            msg += f'\n\nErrors ({len(errors)}):\n' + '\n'.join(errors[:10])
            if len(errors) > 10:
                msg += f'\n... and {len(errors) - 10} more'

        info_dialog(self.gui, 'Conversion Complete', msg, show=True)

        if converted_covers > 0:
            self.gui.library_view.model().refresh_ids(book_ids)
            self.gui.cover_flow.dataChanged()
            self.gui.tags_view.recount()
