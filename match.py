#!/usr/bin/env python3

# author: @oguzserbetci

from collections import defaultdict
import xml.etree.ElementTree as ET
from tqdm import tqdm
import tarfile as tf
import shutil
import pickle
import glob
import gzip
import sys
import re
import os

def find_overlapping_files(path=''):
    files = glob.glob(path+'*.xml.gz')

    dic = defaultdict(dict)
    # 1. Loop over all ces files in path (e.g. de-en.xml.gz) to find overlapping files.
    # 2. Create a dictionary containing matching filenames
    # example dictionary output:
    # {
    #   'en/1921/12349/5775558.xml.gz': {
    #       'de': 'de/1921/12349/5510195.xml.gz',
    #       'es': 'es/1921/12349/4260047.xml.gz',
    #       'et': 'et/1921/12349/5184442.xml.gz',
    #       'fi': 'fi/1921/12349/3676439.xml.gz',
    #       'nl': 'nl/1921/12349/3683372.xml.gz',
    #       'sv': 'sv/1921/12349/5510194.xml.gz'
    #   }
    # }
    print('Found files {}'.format(files))
    for i, f in enumerate(files):
        print('Processing {} | {}/{}'.format(f, i+1, len(files)))
        with gzip.open(f, 'rt') as fl:
            tree = ET.parse(fl)
            root = tree.getroot()
            linkGrps = root.findall('linkGrp')
            for linkGrp in tqdm(linkGrps, desc=f, bar_format='{desc}{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt}'):
                fromDoc = linkGrp.get('fromDoc')
                toDoc = linkGrp.get('toDoc')

                # fromDoc is always english
                tmp = toDoc
                toDoc = toDoc if not toDoc.startswith('en') else fromDoc
                fromDoc = fromDoc if fromDoc.startswith('en') else tmp
                dic[fromDoc].update({toDoc[:2]:toDoc})

    # 3. Save the dictionary in a file
    f = open('file_ids', 'wb')
    pickle.dump(dic,f)
    f.close()
    return dic

def load_dictionary():
    with open('file_ids', 'rb') as file_ids:
        p = pickle.load(file_ids)
        return p

def gather_files(dic, langs, raw_input, output='overlap'):
    missing = False
    files_used = open('used_file_ids', 'w')
    missing_ids = open('missing_file_ids', 'w')

    for k, v in tqdm(dic.items(), desc='copying files', bar_format='{desc}{percentage:3.0f}%|{bar}|{n_fmt}/{total_fmt}'):
        filestocopy = list(v.items()) + [('en', k)]
        if set(langs).issubset({f[0] for f in filestocopy}):
            for key, value in filestocopy:
                if key not in langs:
                    continue
                try:
                    r_file_path = '/'.join(value.split('/')[:-1])
                    source_file = raw_input + '/' + value
                    outpath = output + '/'

                    os.makedirs(outpath+r_file_path, exist_ok=True)
                    shutil.copy(source_file, outpath+value)
                    files_used.write("{0}\n".format(value))

                except FileNotFoundError: # es & tr tarfiles were corrupted, missing some stuff
                    print('missing:', value)
                    missing = True
                    missing_ids.write("{0}\n".format(value))

    files_used.close()
    missing_ids.close()
    return missing

def recover_missing_files(xml_input, target_suffix='-o'):
    # recover missing files by processing respective tokenized files
    with open('missing_file_ids', 'r') as m:
        for filename in m:
            filename_ = filename[:-1].split('/')
            tknzd = xml_input + '/' + filename[:-1]
            target_file = '/'.join([target_suffix] + filename_[:-1] + ["_missing_" + filename_[-1]])
            with gzip.open(tknzd, 'rt', encoding='utf-8') as source:
                with gzip.open(target_file, 'wt', encoding='utf-8') as target:
                    sentence = []
                    for line in source:
                        if "<w" in line:
                            sentence.append(re.split("[><]", line)[-3])
                        elif "<s" in line or "</s>" in line or re.search('<time id=\"T\d+E', line):
                            if sentence:
                                target.write(' '.join(sentence) + '\n')
                            target.write(line)
                            sentence[:] = []
                        else:
                            target.write(line)
            print('Wrote ' + target_file)

def main():
    ces_path, target_path, langs, raw_input, xml_input = sys.argv[1:6]
    langs = langs.split(',')

    dic = find_overlapping_files(ces_path)
    missing = gather_files(dic, langs, raw_input, outpath)
    if missing:
        print('Recovering mising files')
        recover_missing_files(xml_input, outpath)

if __name__ == '__main__':
    main()
