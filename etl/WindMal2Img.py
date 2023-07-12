"@author: NavinKumarMNK"
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import binascii
from collections import defaultdict
from PIL import Image
import numpy as np
import pefile
import utils.utils as utils

def get_width(size_kb):
    if size_kb < 10:
        width = 32
    elif 10 <= size_kb < 30:
        width = 64
    elif 30 <= size_kb < 60:
        width = 128
    elif 60 <= size_kb < 100:
        width = 256
    elif 100 <= size_kb < 200:
        width = 384
    elif 200 <= size_kb < 500:
        width = 512
    elif 500 <= size_kb < 1000:
        width = 768
    else:
        width = 1024

    return width

def load_1d_pe(pe_file, max_size=80):
    # Convert a binary file to a 1d array by reading byte values.
    file_size = os.stat(pe_file).st_size >> 20  # in MB
    if file_size < max_size:

        # Read the binary file in hex
        with open(pe_file, 'rb') as fp:
            hexstring = binascii.hexlify(fp.read())

            # Convert hex string to byte array
            # 2 hex numbers give up to 256 (1 byte) in decimal
            byte_list = [int(hexstring[i: i + 2], 16) for i in
                         range(0, len(hexstring), 2)]

            return np.array(byte_list, dtype=np.uint8)


def get_pe_info(pe_file):
    
    feat = defaultdict(int)
    pe = pefile.PE(pe_file)
    optional_header_size = pe.OPTIONAL_HEADER.SizeOfHeaders
    first_section_offset = pe.sections[0].PointerToRawData
    header_size = optional_header_size + first_section_offset
    feat['file_size'] = os.stat(pe_file).st_size >> 20  # in MB
    feat['header_size'] = header_size
    feat['data_off'] = pe.sections[0].PointerToRawData
    feat['data_size'] = pe.sections[0].SizeOfRawData

    
    return feat

def set_color(pe_info, pe_b, pe_r, pe_g):
    # HEADER -> red
    s0_end = pe_info['header_size']
    pe_r[0: s0_end] = pe_b[0:s0_end]
    pe_b[0: s0_end] = 0

    # DATA -> green
    s7_idx = pe_info['data_off']
    e7_idx = s7_idx + pe_info['data_size']
    pe_g[s7_idx:e7_idx] = pe_b[s7_idx:e7_idx]
    pe_b[s7_idx:e7_idx] = 0

    return pe_r, pe_g


def get_linear(pe_array, size_kb):
    width = get_width(size_kb)
    height = int(len(pe_array) / width)

    pe_array = pe_array[:height * width]  # trim array to 2-D shape
    pe_array_2d = np.reshape(pe_array, (height, width))

    return pe_array_2d


def create_linear_image(pe_path:str, ):
    '''
    @format : {hash_value}.exe
    '''
    file_name = pe_path.split('/')[-1].split('.')[0]
    save_img = utils.TEMP_PATH + '/image/RGB/' + file_name + ".png"
    print(pe_path)
    pe_info = get_pe_info(pe_path)

    pe_b = load_1d_pe(pe_path)
    pe_r = np.zeros(len(pe_b), dtype=np.uint8)
    pe_g = np.zeros(len(pe_b), dtype=np.uint8)
    pe_r, pe_g = set_color(pe_info, pe_b, pe_r, pe_g)

    file_kb = int(os.path.getsize(pe_path) / 1000)
    b_c = get_linear(pe_b, file_kb)
    r_c = get_linear(pe_r, file_kb)
    g_c = get_linear(pe_g, file_kb)

    im = np.stack((r_c, g_c, b_c), axis=-1)
    im = Image.fromarray(im)

    image_size = 256

    im_resized = im.resize(size=(image_size, image_size), resample=Image.Resampling.LANCZOS)  # ANTIALIAS provides higher quality image
    im_resized.save(save_img)


if __name__ == '__main__':
    create_linear_image("putty.exe")
