#!/usr/bin/env python3

# author: @oguzserbetci

from collections import defaultdict
import treetaggerwrapper
from glob import glob
from tqdm import tqdm
from pathlib import Path, PurePath
import json
import gzip
import sys
import os
import argparse

def process(line, lang, tagger=None, exceptions=None):

    if not tagger:
        tagger = treetaggerwrapper.TreeTagger(TAGLANG=lang)

    tagged = treetaggerwrapper.make_tags(tagger.tag_text(line), True)
    l = []
    for i in tagged:
        flag = True
        if exceptions:
            for e in exceptions:
                if i[0].lower().startswith(e):
                    l.append(e)
                    flag = False
                    break
        if flag:
            l.append(degender(i[2], i[1], lang))
    return l

def degender(w, t, lang):
    if t in ['PP', 'PP$']:
        if w in ['he', 'she']:
            return 'it'
        if w in ['him', 'her']:
            return 'it'
        if w in ['his', 'hers', 'its']:
            return 'its'
        if w in ['his', 'hers', 'its']:
            return 'its'
        if w in ['himself', 'herself', 'itself']:
            return 'itself'
    if t == 'det__art' and w in ['de', 'het']:
        return 'de'
    if t == 'pronpers':
        if w in ['hij', 'hem', 'zij', 'haar', 'het', 'het', 'ze']:
            return 'perp3s'
        if w in ['zij', 'ze', 'hun', 'hen', 'die', 'hun', 'hen']:
            return 'perp3p'
    if t in ['pronposs', 'det__poss']:
        if w in ['zijn', 'haar', 'zijn', 'zijne', 'hare', 'zijne']:
            return 'posp3s'
        if w in ['hun', 'hunne']:
            return 'posp3p'
    if t in ['prondemo', 'det__demo']:
        if w in ['dit']:
            return 'deze'
        if w in ['dat']:
            return 'die'
    return w

def process_files(source_path, target_path, languages=['en'], exception_file=None):
    source_path = Path(source_path)
    target_path = Path(target_path)
    for l in languages:
        tagger = treetaggerwrapper.TreeTagger(TAGLANG=l)
        ipath = Path(l) / '**/*.gz'
        paths = list(source_path.glob(str(ipath)))
        exceptions = None
        if exception_file:
            with open(exception_file) as f:
                exceptions = json.loads(f.read())[l]
                if isinstance(exceptions, dict):
                    exception_terms = []
                    for k in exceptions:
                        exception_terms += exceptions[k]
                    exceptions = exception_terms
        for f_i, path in tqdm(enumerate(paths), desc=l, total=len(paths)):
            with gzip.open(path, 'rt') as source:
                target_file = target_path / path.relative_to(source_path)
                os.makedirs(target_file.parent, exist_ok=True)

                with gzip.open(target_file, 'wt') as target:
                    for line in source:
                        if line.startswith('\n') or line.startswith('\t') or line.startswith(' ') or line.startswith('<'):
                            continue
                        p = ' '.join(process(line, l, tagger, exceptions))

                        target.write(p + '\n')

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("source_path", 
        help="Relative path of source files directory")
    parser.add_argument("target_path", 
        help="Path for output files (including directory creation)")
    parser.add_argument("-l", "--languages", 
        help="Comma-separated list of language alpha2 codes (N.B. expected in root level directory for source_path)",
        default="de,es,nl,en")
    parser.add_argument("-e", "--exception_file", 
        help="JSON file with exception words not to be lemmatized. See words_to_test.json for format.")
    args = parser.parse_args()
    
    process_files(args.source_path, args.target_path, 
        args.languages.split(','), args.exception_file)

if __name__ == '__main__':
    main()
