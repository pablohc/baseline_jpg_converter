#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Shared conversion logic for Baseline JPEG Converter.
Used by both Calibre plugin and standalone script.
"""

import re
import zipfile


class EpubConverterShared:
    """Shared conversion logic for EPUB processing."""

    # Maximum dimensions for resized images
    MAX_WIDTH = 480
    MAX_HEIGHT = 800

    def convert_image_to_baseline(self, image_data):
        """Convert image to baseline JPEG format with max dimensions of 480x800."""
        try:
            from PIL import Image
            from io import BytesIO

            img = Image.open(BytesIO(image_data))

            # Convert to RGB
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize if image exceeds max dimensions
            if img.width > self.MAX_WIDTH or img.height > self.MAX_HEIGHT:
                # Calculate scaling factor to fit within bounds
                ratio = min(self.MAX_WIDTH / img.width, self.MAX_HEIGHT / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)

            output = BytesIO()
            img.save(output, format='JPEG', quality=85, progressive=False, optimize=False)
            return output.getvalue()
        except Exception:
            return None

    def fix_svg_images(self, xhtml_content, xhtml_path):
        """
        Fix ALL SVG-wrapped images in EPUB pages.
        Replaces <svg><image xlink:href="..."/></svg> with <img src="..."/>.
        Returns (fixed_content, fixed_count).
        """
        # Check if this content has SVG with xlink:href images
        if '<svg' not in xhtml_content or 'xlink:href' not in xhtml_content:
            return xhtml_content, 0

        fixed_count = 0
        result = xhtml_content

        # Pattern 1: SVG with xlink:href attribute
        svg_pattern = re.compile(
            r'<svg[^>]*>.*?<image[^>]*xlink:href\s*=\s["\']([^"\']+)["\'][^>]*/?>.*?</svg>',
            re.DOTALL | re.IGNORECASE
        )

        for match in svg_pattern.finditer(result):
            svg_tag = match.group(0)
            image_path = match.group(1)

            # Extract title if present for alt text
            title_match = re.search(r'<title[^>]*>([^<]*)</title>', svg_tag, re.IGNORECASE)
            alt_text = title_match.group(1).strip() if title_match else ''

            # Extract class from SVG if present
            class_match = re.search(r'class=["\']([^"\']*)["\']', svg_tag, re.IGNORECASE)
            svg_class = f' class="{class_match.group(1)}"' if class_match else ''

            # Build replacement img tag
            img_tag = f'<img src="{image_path}" alt="{alt_text}"{svg_class}/>'
            result = result.replace(svg_tag, img_tag)
            fixed_count += 1

        # Pattern 2: SVG with href attribute (without xlink:)
        svg_pattern2 = re.compile(
            r'<svg[^>]*>\s*<image[^>]*href=["\']([^"\']+)["\'][^>]*/?>\s*</svg>',
            re.DOTALL | re.IGNORECASE
        )

        for match in svg_pattern2.finditer(result):
            svg_tag = match.group(0)
            image_path = match.group(1)
            img_tag = f'<img src="{image_path}" alt=""/>'
            result = result.replace(svg_tag, img_tag)
            fixed_count += 1

        return result, fixed_count

    def ensure_cover_meta(self, opf_content):
        """Ensure OPF has correct <meta name="cover" content="X"/>."""
        # Find cover image id from manifest
        cover_id = None

        # Try 1: find item with properties="cover-image"
        match = re.search(r'<item[^>]+id="([^"]+)"[^>]+properties="[^"]*cover-image[^"]*"', opf_content)
        if match:
            cover_id = match.group(1)

        if not cover_id:
            match = re.search(r'<item[^>]+properties="[^"]*cover-image[^"]*"[^>]+id="([^"]+)"', opf_content)
            if match:
                cover_id = match.group(1)

        # Try 2: find item with "cover" in href and image media-type
        if not cover_id:
            match = re.search(r'<item[^>]+id="([^"]+)"[^>]+href="[^"]*cover[^"]*"[^>]*media-type="image/', opf_content, re.IGNORECASE)
            if match:
                cover_id = match.group(1)

        if not cover_id:
            match = re.search(r'<item[^>]+href="[^"]*cover[^"]*"[^>]+id="([^"]+)"[^>]*media-type="image/', opf_content, re.IGNORECASE)
            if match:
                cover_id = match.group(1)

        # Try 3: find item with "cover" in id and image media-type
        if not cover_id:
            match = re.search(r'<item[^>]+id="([^"]*cover[^"]*)"[^>]+media-type="image/', opf_content, re.IGNORECASE)
            if match:
                cover_id = match.group(1)

        if not cover_id:
            return opf_content, False

        # Check if cover meta exists
        meta_match = re.search(r'<meta\s+name=["\']cover["\']\s+content=["\']([^"\']+)["\']', opf_content)
        if meta_match:
            current_value = meta_match.group(1)
            if '/' in current_value or current_value != cover_id:
                opf_content = re.sub(
                    r'<meta\s+name=["\']cover["\']\s+content=["\'][^"\']+["\']\s*/?>',
                    f'<meta name="cover" content="{cover_id}" />',
                    opf_content
                )
                return opf_content, True
            return opf_content, False

        # Add missing cover meta
        new_meta = f'    <meta name="cover" content="{cover_id}"/>\n  </metadata>'
        opf_content = opf_content.replace('</metadata>', new_meta)

        return opf_content, True
