Code & analysis for the [WiNLP 2017](http://www.winlp.org/winlp-workshop/) talk 'Grammatical gender associations outweigh topical gender bias in crosslinguistic word embeddings'.

# Installation

## Treetagger

Install [Treetagger](http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/) by following the linked instructions.

Once installed, set the TAGDIR environment variable so that the python wrapper library can find it:

```bash
$ echo "export TAGDIR=<path/to/your/Treetagger/installation>" >> ~/.bash_profile
```

## Python

Required packages can be found in the file `environment.yml`.

If using the Anaconda distribution, these can be imported directly as a conda environment.

## R

Run the following command to install the R packages required for analysis:

```bash
$ Rscript -e 'install.packages(c("tidyjson", "ggplot2", "magrittr", "data.table"), repos="http://cran.us.r-project.org")'
```

# Download subtitles

Download, unzip, and untar parallel corpora files from [OpenSubtitles](http://opus.lingfil.uu.se/OpenSubtitles2016):

```bash
$ curl -O -J  http://opus.lingfil.uu.se/OpenSubtitles2016/de.raw.tar.gz && gunzip de.raw.tar.gz && tar -xf de.raw.tar
$ curl -O -J  http://opus.lingfil.uu.se/OpenSubtitles2016/en.raw.tar.gz && gunzip en.raw.tar.gz && tar -xf en.raw.tar
$ curl -O -J http://opus.lingfil.uu.se/OpenSubtitles2016/es.raw.tar.gz && gunzip es.raw.tar.gz && tar -xf es.raw.tar # corrupted! see below
$ curl -O -J http://opus.lingfil.uu.se/OpenSubtitles2016/nl.raw.tar.gz && gunzip nl.raw.tar.gz && tar -xf nl.raw.tar
```
The 'raw' Spanish corpus file is corrupted, so you have to download the tokenized version as well:

```bash
$ curl -O -J  http://opus.lingfil.uu.se/OpenSubtitles2016/es.tar.gz && gunzip es.tar.gz && tar -xf es.tar
```

Download mapping files:

```bash
$ curl -O -J http://opus.lingfil.uu.se/OpenSubtitles2016/xml/de-en.xml.gz
$ curl -O -J http://opus.lingfil.uu.se/OpenSubtitles2016/xml/en-es.xml.gz
$ curl -O -J http://opus.lingfil.uu.se/OpenSubtitles2016/xml/en-nl.xml.gz
```

# Get parallel texts

Use `match.py` to identify files from the intersection set of parallel texts and copy them to another folder. You need to have the ces archive intact and individual language files unzipped (see first step). 

This script will handle the missing corrupted files from Spanish by generating a file `missing_file_ids` and taking replacements from the tokenized file. If you need to re-run `match.py`, delete this file so new missing ids can be stored.

```bash
# command to run:
$ python3 match.py ./ overlap de,en,es,nl OpenSubtitles2016/raw OpenSubtitles/xml
```

# Generate lemmatized (= degendered) corpus files

```bash
# usage:
$ python degender.py -h
# command to run:
$ python3 degender.py overlap degendered -l de,es,en,nl -e words_to_test.json
```

# Train models

`train_w2v.py` can read a folder recursively to build a model on all files. 

Default settings are CBOW + negative sampling; use flags to specify skip-gram and hierarchical softmax.  

For your convenience, here are the commands to train models for each condition (language x corpus type):

```bash
# usage:
$ python3 train_w2v.py -h

# english
$ python3 train_w2v.py overlap/en w2v-models/unprocessed/en/en-vectors.txt
$ python3 train_w2v.py degendered/en w2v-models/degendered/en/en-g-vectors.txt
# spanish
$ python3 train_w2v.py overlap/es w2v-models/unprocessed/es/es-vectors.txt
$ python3 train_w2v.py degendered/es w2v-models/degendered/es/es-g-vectors.txt
# german
$ python3 train_w2v.py overlap/de w2v-models/unprocessed/de/de-vectors.txt
$ python3 train_w2v.py degendered/de w2v-models/degendered/de/de-g-vectors.txt
# dutch
$ python3 train_w2v.py overlap/nl w2v-models/unprocessed/nl/nl-vectors.txt
$ python3 train_w2v.py degendered/nl w2v-models/degendered/nl/nl-g-vectors.txt
```

# Evaluate

## Run WEAT

The Word Embedding Association Test (WEAT, implemented in `WEAT.py`), is used to evaluate specific parallel vocabulary in each language.

The vocabulary used for evaluation can be found in `words_to_test.json`. The tests to run with WEAT can be specified in a config file, formatted as in `evaluation_config.json`, with the following fields:

- tests: an array of objects - each object specifies a test to be run. Each test object has three attributes:
  - name: the name of the test (will be used as the key in results storage)
  - attributes: an array of 2 strings specifying attribute word sets. each string should be the key to an array of words in each of the languages to be tested.
  - targets: an array of 2 strings specifying target word sets. each string should be the key to an array of words in each of the languages to be tested.
- terms: source of vocabulary to be tested for each language. this can be EITHER
  - a string specifying another file, e.g. `words_to_test.json`, OR
  - a hash formatted as in the file `words_to_test.json`.
- model_path: a hash specifying relative paths to load models based on either the unprocessed corpus or the degendered corpus. Note that it assumes each directory will have individual subdirectories for each language, e.g. path/to/degendered/models/en, path/to/degendered/models/de, etc.

To replicate the findings in the paper, run the following:
```bash
#usage: python3 model_eval.py -h
python3 model_eval.py evaluation_config.json results.json -w
```

Format of output file, i.e. `results.json`:

- name, attributes, targets: taken from specified test, see description above
- language: alpha2 language code of model and vocabulary
- corpus_type: either 'unprocessed' or 'lemmatized', depending on the corpus that was used to train the model
- model_index: index indicating on which run this model was trained (i.e. if 10 models were trained for a particular condition, model_index will range from 0 to 9)
- results: hash of WEAT test results, with the following fields (calculated as per Caliskan et al, please refer to their paper for details):
  - test_stat: the WEAT test statistic
  - pval: *p-value* estimated based on WEAT test statistic
  - effect_size: estimated effect size
  - words: array with bias data (skew toward first attribute) for each individual tested word

## Analyze results

Run `analysis.R` to reproduce findings from the abstract:

- results_summary.csv - summary of test results by condition
- plot_overall.png - plot of overall results (corresponds to Figure 1 in abstract)
- plot_words_topic.png - plot lemmatization effects on topical gender bias of individual words
- plot_words_gramm.png - plot lemmatization effects on grammatical gender bias of individual words

```bash
Rscript analysis.R results.json
```
