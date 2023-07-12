'@author:NavinKumarMNK'
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import utils.utils as utils

import numpy as np
from PIL import Image
import array
import cv2

def get_byteplot_image(file_path):
    ln = os.path.getsize(file_path)
    file_size = ln / 1024
    print(file_size)
    f = open(file_path, 'rb')
    if file_size < 10:
        col_size = 32
    elif file_size < 30:
        col_size = 64
    elif file_size < 60:
        col_size = 128
    elif file_size < 100:
        col_size = 256
    elif file_size < 200:
        col_size = 384
    elif file_size < 500:
        col_size = 512
    elif file_size < 1000:
        col_size = 768
    else:
        col_size = 1024

    rem = ln % col_size
    if rem != 0:
        ln -= rem
    a = array.array('B')
    a.fromfile(f, ln)
    f.close()
    if ln < col_size:
        g = np.expand_dims(np.pad(a, ((0, col_size - ln),), mode='constant'), 0)
    else:
        g = np.reshape(a, (-1, col_size))
    im = np.array(g)
    im = Image.fromarray(im)
    im_resized = im.resize((256, 256))
    im = np.array(im_resized)
    return im

def get_bigram_dct_image(file_path):
    ln = os.path.getsize(os.path.abspath(file_path))
    file_size = ln / 1024
    f = open(file_path, 'rb')
    if file_size < 10:
        col_size = 32
    elif file_size < 30:
        col_size = 64
    elif file_size < 60:
        col_size = 128
    elif file_size < 100:
        col_size = 256
    elif file_size < 200:
        col_size = 384
    elif file_size < 500:
        col_size = 512
    elif file_size < 1000:
        col_size = 768
    else:
        col_size = 1024

    rem = ln % col_size
    if rem != 0:
        ln -= rem
    a = array.array('B')
    a.fromfile(f, ln)
    f.close()
    if ln < col_size:
        g = np.expand_dims(np.pad(a, ((0, col_size - ln),), mode='constant'), 0)
    else:
        g = np.reshape(a, (-1, col_size))
    im11 = np.uint8(g)
    im11_vect = im11.reshape((1, im11.shape[0] * im11.shape[1]))[0]
    vhex = np.vectorize(hex)
    im11_hex = vhex(im11_vect)
    bi_gram_disbn = np.zeros(int('ffff', 16) + 1)
    for k1 in range(len(im11_hex) - 1):
        temmp = im11_hex[k1][2:4] + im11_hex[k1 + 1][2:4]
        hexx = int(temmp, 16)
        bi_gram_disbn[hexx] = bi_gram_disbn[hexx] + 1
    else:
        bi_gram_disbn[0] = 0
        temp_norm = bi_gram_disbn / bi_gram_disbn.max()
        img_2d = np.reshape(temp_norm, (256, 256))
        dst = cv2.dct(img_2d)
        dst_norm = (dst - dst.min()) / (dst.max() - dst.min())
        img_tran = np.uint8(dst_norm * 255.0)
        im = np.array(img_tran)

    im = Image.fromarray(im)
    im_resized = im.resize((256, 256))
    im_resized = np.array(im_resized)
    return im_resized

def get_mal2img_bb(file_path):
    byteplot_im = get_byteplot_image(file_path)
    bigram_dct_im = get_bigram_dct_image(file_path)
    # two channel image
    im_data = np.stack((byteplot_im, bigram_dct_im), axis=2)
    im_data = im_data.transpose((2, 0, 1))

    # save the file to disk
    im = Image.fromarray(im_data)
    file_name = file_path.split('/')[-1].split('.')[0]
    save_path = save_img = utils.TEMP_PATH + '/image/BB/' + file_name + ".png"
    im.save(save_path)

if __name__ == '__main__':
    file_path = utils.ROOT_PATH + '/temp/malware/win/putty.exe'
    mal2img_bb = get_mal2img_bb(file_path)
    Image.fromarray(mal2img_bb).show()