#!/usr/bin/env python3

# author: @kmccurdy

# for usage:
# python train_w2v.py -h

import gensim, logging, re, os, glob, string, sys, gzip, io, argparse
from tqdm import tqdm
 
parser = argparse.ArgumentParser()
parser.add_argument("source_path", 
    help="Relative path of source files directory")
parser.add_argument("target_filename", 
    help="Path and filename template for output files (including directory creation)")
parser.add_argument("-m", "--softmax", 
    help="Flag: use hierarchical softmax instead of negative sampling",
    action="store_true")
parser.add_argument("-s", "--skipgram", 
    help="Flag: use skipgram instead of CBOW",
    action="store_true")
parser.add_argument("-n","--n_runs", 
    help="Number of model runs. Run number (i.e. 1-N) will be encoded in the name of each stored set of vectors.",
    type=int,
    default=10)
parser.add_argument("-w", "--workers", 
    help="Number of workers to use for training",
    type=int,
    default=4)

class Sentences(object):
  def __init__(self, dirname):
    self.files = [f for f in glob.glob(dirname + '/**/*', recursive=True) if os.path.isfile(f)]

  def process_words(self, line):
    text = re.sub('<[^<]+?>', '', line).strip(string.punctuation)
    return [w.strip(string.punctuation).lower() for w in text.split()]

  def __iter__(self):
    for fname in self.files:
      if fname.endswith("gz"):
        with io.TextIOWrapper(io.BufferedReader(gzip.open(fname))) as file:
          for line in file:
            words = self.process_words(line)
            if words:
              yield words
      else:
        with open(fname) as file:
          for line in file:
            words = self.process_words(line)
            if words:
              yield words
 
def main():

  args = parser.parse_args()
  program = os.path.basename(sys.argv[0])
  logger = logging.getLogger(program)

  os.makedirs('logs',exist_ok=True)
  logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                     filename='logs/' + program + '.' + args.source_path.replace('/','_') + '.log')
  logging.root.setLevel(level=logging.INFO)
  logger.info("running %s" % ' '.join([program, args.source_path, 
    args.target_filename, str(args.n_runs)]))

  os.makedirs(os.path.dirname(args.target_filename), exist_ok=True)
  target_path, target_filetype = args.target_filename.split('.')
  target_filetype = target_filetype if target_filetype else "txt"
  logger.debug("output: %s %s" % (target_path, target_filetype))

  sentences = Sentences(args.source_path) 
  logger.info("training on {} files".format(len(sentences.files)))
  for run in tqdm(range(args.n_runs), total=args.n_runs):
    model = gensim.models.Word2Vec(sentences, 
      workers=args.workers, 
      sg=args.skipgram, 
      hs=args.softmax)
    #model.save(target_path+"_binary_"+str(run)) #uncomment to save binary model
    outfile = target_path+str(run)+"."+target_filetype
    model.wv.save_word2vec_format(outfile, binary=False)
    logger.info("   Saved %s " % outfile)

if __name__ == '__main__':
  main()
