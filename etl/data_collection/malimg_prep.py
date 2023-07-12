
import os
import shutil
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import utils.utils as utils
from PIL import Image

def create_folders_and_copy_files(root_dir):
    new_dir = os.path.join(os.path.dirname(root_dir), 'malbinimg')
    if not os.path.exists(new_dir):
        os.mkdir(new_dir)

    size_count = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            for sub_dirpath, sub_dirname, sub_filenames in os.walk(os.path.join(dirpath, dirname)):
                for subdir in sub_dirname:
                    print(subdir)
                    new_sub_dir = os.path.join(new_dir, subdir)
                    if not os.path.exists(new_sub_dir):
                        os.mkdir(new_sub_dir)
                    for filename in os.listdir(os.path.join(sub_dirpath, subdir)):
                        src = os.path.join(sub_dirpath, subdir, filename)
                        dst = os.path.join(new_sub_dir, filename)
                        if not os.path.exists(dst):
                            shutil.copy(src, dst)
                        else:
                            print(f"File {filename} already exists in {new_sub_dir}")
                        
                        with Image.open(src) as img:
                            size = f'{img.width}x{img.height}'
                            if size not in size_count:
                                size_count[size] = 1
                            else:
                                size_count[size] += 1
                    

    for size, count in size_count.items():
        print(f'{count} images of size {size}')

def extract_folders(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            for sub_dirpath, sub_dirname, sub_filenames in os.walk(os.path.join(dirpath, dirname)):
                for subdir in sub_dirname:
                    for filename in os.listdir(os.path.join(sub_dirpath, subdir)):
                        src = os.path.join(sub_dirpath, subdir, filename)
                        shutil.move(src, os.path.join(sub_dirpath, filename))
                    
                    os.rmdir(os.path.join(sub_dirpath, subdir))

if (__name__ == '__main__'):
    root_dir = utils.ROOT_PATH + '/dataset/Malware/malware_images'
    #create_folders_and_copy_files(root_dir)
    extract_folders(root_dir)