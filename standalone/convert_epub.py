#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standalone EPUB converter - converts images to baseline JPEG and fixes SVG-wrapped images.
Usage: python convert_epub.py <epub_file_or_directory>

This script uses the shared conversion logic from ../shared/converter.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import shared module
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from shared.converter import EpubConverterShared


class EpubConverter(EpubConverterShared):
    """Extends shared converter with EPUB file processing logic."""

    def convert_epub(self, epub_path):
        """Convert EPUB images to baseline JPEG and fix SVG images."""
        import tempfile
        import shutil
        import zipfile
        import re

        converted_count = 0
        svg_images_fixed = 0
        cover_meta_added = False
        renamed_files = {}

        temp_fd, temp_path = tempfile.mkstemp(suffix='.epub')
        os.close(temp_fd)

        try:
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
                            new_data = self.convert_image_to_baseline(data)
                            if new_data:
                                data = new_data
                                converted_count += 1
                                if filename in renamed_files:
                                    filename = renamed_files[filename]

                        # Fix SVG images in HTML/XHTML files
                        elif lower_name.endswith(('.xhtml', '.html', '.htm')):
                            try:
                                text = data.decode('utf-8')
                                text, fixed_count = self.fix_svg_images(text, filename)
                                svg_images_fixed += fixed_count

                                # Update image references for renamed files
                                for old_name, new_name in renamed_files.items():
                                    old_basename = old_name.split('/')[-1]
                                    new_basename = new_name.split('/')[-1]
                                    text = text.replace(old_basename, new_basename)
                                    text = text.replace(old_name, new_name)
                                data = text.encode('utf-8')
                            except Exception as e:
                                print(f"  Warning: Could not process {filename}: {e}")

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
                                text, meta_added = self.ensure_cover_meta(text)
                                if meta_added:
                                    cover_meta_added = True

                                data = text.encode('utf-8')
                            except Exception as e:
                                print(f"  Warning: Could not process OPF: {e}")

                        # Write file to new EPUB
                        if item.filename == 'mimetype':
                            zout.writestr(item, data, compress_type=zipfile.ZIP_STORED)
                        else:
                            new_info = zipfile.ZipInfo(filename)
                            new_info.compress_type = zipfile.ZIP_DEFLATED
                            zout.writestr(new_info, data)

            # Generate output filename with .x4.epub extension
            output_path = str(epub_path).replace('.epub', '.x4.epub')
            if output_path == str(epub_path):
                output_path = str(epub_path) + '.x4.epub'
            shutil.move(temp_path, output_path)

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

        return converted_count, svg_images_fixed, cover_meta_added


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python convert_epub.py <epub_file_or_directory>")
        print("\nExamples:")
        print("  python convert_epub.py book.epub")
        print("  python convert_epub.py /path/to/epubs/")
        sys.exit(1)

    converter = EpubConverter()
    target = Path(sys.argv[1])

    # Collect EPUB files
    epub_files = []
    if target.is_file():
        if target.suffix.lower() == '.epub':
            epub_files.append(target)
    elif target.is_dir():
        epub_files.extend(target.glob('*.epub'))
        epub_files.extend(target.glob('**/*.epub'))

    if not epub_files:
        print(f"No EPUB files found at: {target}")
        sys.exit(1)

    print(f"Found {len(epub_files)} EPUB file(s) to process.\n")

    total_converted = 0
    total_svg_fixed = 0
    total_meta_added = 0
    errors = []

    for epub_path in epub_files:
        print(f"Processing: {epub_path.name}")
        try:
            converted, svg_fixed, meta_added = converter.convert_epub(str(epub_path))
            total_converted += converted
            total_svg_fixed += svg_fixed
            total_meta_added += meta_added

            # Generate output filename
            output_name = epub_path.stem + '.x4.epub'
            if converted > 0:
                print(f"  Converted {converted} image(s) to baseline JPEG")
            if svg_fixed > 0:
                print(f"  Fixed {svg_fixed} SVG-wrapped image(s)")
            if meta_added:
                print(f"  Added cover meta tag")
            if converted == 0 and svg_fixed == 0 and not meta_added:
                print(f"  No changes needed")
            print(f"  Created: {output_name}")
        except Exception as e:
            errors.append(f"{epub_path.name}: {str(e)}")
            print(f"  ERROR: {e}")
        print()

    # Summary
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total images converted: {total_converted}")
    print(f"Total SVG images fixed: {total_svg_fixed}")
    print(f"Total cover metas added: {total_meta_added}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")

    print("\nDone!")


if __name__ == '__main__':
    main()
