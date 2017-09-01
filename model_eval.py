#!/usr/bin/env python3

# author: @kmccurdy

from WEAT import WEAT
from degender import process
import json, logging, sys, os, argparse, treetaggerwrapper


# iterate over comparisons using local config

class W2vTests(object):

  def __init__(self, config, result_file, langs, include_word_diffs=True):
    self.conf = {}
    self.configFile = config
    self.results = []
    self.resultFile = result_file
    self.word_diffs = include_word_diffs
    self.langs = langs
    self.lang = ""
    self.terms = {}
    self.term_data = {}
    self.mods_path = ""
    self.mods = []
    self.mod_index = 0
    self.tagger = {}
    self.model = {}
    self.tests = []
    

  def load_config(self):
    with open(self.configFile) as f:
      self.conf = json.loads(f.read())

  def load_terms(self):
    if isinstance(self.conf['terms'], dict):
      self.terms = self.conf['terms']
    else:
      with open(self.conf['terms']) as f:
        self.terms = json.loads(f.read())

  def write_results(self, resultFile=None):
    if not resultFile:
      resultFile = self.resultFile
    with open(resultFile, "w") as f:
      f.write(json.dumps(self.results))

  def setup_lang(self, lang):
    if lang not in self.langs:
      raise ValueError("Language not included during initialization")
    self.lang = lang
    self.tagger = treetaggerwrapper.TreeTagger(TAGLANG=lang)
    self.term_data = self.terms[lang].copy()

  def setup_models(self, degendered=""):
    if degendered:
      self.mods_path = self.conf["model_path"]["degendered_dir"]      
      for w_set in self.term_data:
        self.term_data[w_set] = process(self.term_data[w_set], self.lang, self.tagger)
    else:
      self.mods_path = self.conf["model_path"]["unprocessed_dir"]
    self.mods_path += "/" 
    self.mods_path += self.lang
    self.mods = os.listdir(self.mods_path)


  def setup_model(self, mod):
    self.mod_index = self.mods.index(mod)
    self.model = WEAT(self.mods_path + "/" + mod) 

  def get_word_diffs(self, targ1, targ2, attr1, attr2, targ_labels):
    a1 = self.model.check_vocab(attr1)
    a2 = self.model.check_vocab(attr2)
    res = [{"word": w, "word_set": targ_labels[0],
            "attr1_bias": self.model.sim_set_diff(w.lower(), a1, a2)} \
            for w in targ1 if w.lower() in self.model.model]
    res += [{"word": w, "word_set": targ_labels[1],
            "attr1_bias": self.model.sim_set_diff(w.lower(), a1, a2)} \
            for w in targ2 if w.lower() in self.model.model]
    return(res)

  def run_test(self, test, word_diffs=True):
    attr1, attr2 = [self.term_data[attr] for attr in test["attributes"]]
    targ1, targ2 = [self.term_data[targ] for targ in test["targets"]]
    res = {}
    res["test_stat"], res["pval"], res["effect_size"] = \
      self.model.weat(targ1, targ2, attr1, attr2)
    logging.info('  Finished test - result {0:.2f}, pval {1:.3f}, effect size {2:.2f}'.format(
            res["test_stat"], res["pval"], res["effect_size"]))
    if word_diffs:
      res['words'] = self.get_word_diffs(targ1, targ2, attr1, attr2, test["targets"])
    return(res)

  def run_tests(self):
    self.tests = self.conf["tests"]
    for lang in self.langs:
      logging.info("Lang: " + lang)
      self.setup_lang(lang)
      for corpus_type in ["", "lemmatized"]:
        logging.info("  Model type: " + str(corpus_type))
        self.setup_models(corpus_type)
        for mod in self.mods:
          logging.info("    Model: " + mod)
          self.setup_model(mod)
          for test in self.tests:
            res = test.copy()
            res["language"] = lang
            res["corpus_type"] = corpus_type
            res["model_index"] = self.mod_index
            logging.info("      Running test: " + test['name'])
            res["results"] = self.run_test(test)
            self.results.append(res)
            
  def runW2vTests(self):
    self.load_config()
    self.load_terms()
    self.run_tests()
    self.write_results()


def main():

  program = os.path.basename(sys.argv[0])
  logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                     filename='logs/' + program + '.log')
  logging.root.setLevel(level=logging.INFO)

  parser = argparse.ArgumentParser()
  parser.add_argument("config", 
      help="Relative path of config JSON file; see evaluation_config.json for format")
  parser.add_argument("result_file", 
      help="Path for result JSON file")
  parser.add_argument("-l", "--languages", 
      help="Comma-separated list of language alpha2 codes",
      default="de,es,nl,en")
  parser.add_argument("-w", "--word_diffs",
      help="Flag: store results for individual words?",
      action="store_true")
  args = parser.parse_args()

  test_w2v = W2vTests(args.config, args.result_file, \
                          args.languages.split(","), args.word_diffs)
  test_w2v.runW2vTests()




if __name__ == '__main__':
  main()
