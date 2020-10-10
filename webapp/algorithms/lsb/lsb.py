# -*- coding: utf-8 -*-
import os
import sys
from PIL import Image

from webapp.algorithms.lsb.bit import (
    lsb_deinterleave_list,
    lsb_interleave_list,
    roundup,
)

def _str_to_bytes(x, charset=sys.getdefaultencoding(), errors="strict"):
    if x is None:
        return None
    if isinstance(x, (bytes, bytearray, memoryview)):  # noqa
        return bytes(x)
    if isinstance(x, str):
        return x.encode(charset, errors)
    if isinstance(x, int):
        return str(x).encode(charset, errors)
    raise TypeError("Expected bytes")


def get_filesize(path):
    """Returns the file size in bytes of the file at path"""
    return os.stat(path).st_size


def max_bits_to_hide(image, num_lsb):
    """Returns the number of bits we're able to hide in the image using
    num_lsb least significant bits."""
    # 3 color channels per pixel, num_lsb bits per color channel.
    return int(3 * image.size[0] * image.size[1] * num_lsb)


def bytes_in_max_file_size(image, num_lsb):
    """Returns the number of bits needed to store the size of the file."""
    return roundup(max_bits_to_hide(image, num_lsb).bit_length() / 8)


def hide_message_in_image(input_image, message, num_lsb):
    """Hides the message in the input image and returns the modified
    image object.
    """
    # in some cases the image might already be opened
    if isinstance(input_image, Image.Image):
        image = input_image
    else:
        image = Image.open(input_image)

    num_channels = len(image.getdata()[0])
    flattened_color_data = [v for t in image.getdata() for v in t]

    # We add the size of the input file to the beginning of the payload.
    message_size = len(message)
    # return image
    file_size_tag = message_size.to_bytes(bytes_in_max_file_size(image, num_lsb), byteorder=sys.byteorder)
    data = file_size_tag + _str_to_bytes(message)

    if 8 * len(data) > max_bits_to_hide(image, num_lsb):
        raise ValueError(
            f"Only able to hide {max_bits_to_hide(image, num_lsb) // 8} bytes "
            + f"in this image with {num_lsb} LSBs, but {len(data)} bytes were requested"
        )

    flattened_color_data = lsb_interleave_list(flattened_color_data, data, num_lsb)

    # PIL expects a sequence of tuples, one per pixel
    image.putdata(list(zip(*[iter(flattened_color_data)] * num_channels)))
    return image


def hide_data(
    input_image_path, secret_message, steg_image_path, num_lsb, compression_level
):
    image = Image.open(input_image_path)
    image = hide_message_in_image(image, secret_message.encode(), num_lsb)
    image.save(steg_image_path, compress_level=compression_level)


def recover_message_from_image(input_image, num_lsb):
    """Returns the message from the steganographed image"""
    if isinstance(input_image, Image.Image):
        steg_image = input_image
    else:
        steg_image = Image.open(input_image)

    color_data = [v for t in steg_image.getdata() for v in t]

    file_size_tag_size = bytes_in_max_file_size(steg_image, num_lsb)
    tag_bit_height = roundup(8 * file_size_tag_size / num_lsb)

    bytes_to_recover = int.from_bytes(
        lsb_deinterleave_list(
            color_data[:tag_bit_height], 8 * file_size_tag_size, num_lsb
        ),
        byteorder=sys.byteorder,
    )

    maximum_bytes_in_image = (
        max_bits_to_hide(steg_image, num_lsb) // 8 - file_size_tag_size
    )
    if bytes_to_recover > maximum_bytes_in_image:
        raise ValueError(
            f"This image appears to be corrupted.\n"
            + f"It claims to hold {bytes_to_recover} B, "
            + f"but can only hold {maximum_bytes_in_image} B with {num_lsb} LSBs"
        )

    data = lsb_deinterleave_list(
        color_data, 8 * (bytes_to_recover + file_size_tag_size), num_lsb
    )[file_size_tag_size:]
    return data


def recover_data(steg_image_path, num_lsb):
    steg_image = Image.open(steg_image_path)
    data = recover_message_from_image(steg_image, num_lsb)

    return data.decode()