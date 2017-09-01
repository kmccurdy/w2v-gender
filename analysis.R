#!/usr/bin/env Rscript

# usage: analysis.R <path/to/results/file.json>

# output:
# results_summary.csv - summary of test results by condition
# plot_overall.png - plot of overall results (corresponds to Figure 1 in abstract)
# plot_words_topic.png - plot lemmatization effects on topical gender bias of individual words
# plot_words_gramm.png - plot lemmatization effects on grammatical gender bias of individual words

library(data.table)
library(magrittr)
library(ggplot2)
library(tidyjson)

## setup

colors.c = c('#ff8d15', '#25719c', '#b6da36', '#e44d25', '#ffcb17', '#a64884', '#ea7252', '#4c4c45', '#4d9238', '#ee6e87', '#dad6c1', '#40bada')
base_plot = ggplot() +
  scale_color_manual(values=colors.c) +
  scale_fill_manual(values=colors.c) +
  theme_bw() +
  theme(axis.text.x = element_text(angle=45, hjust=1))

args = commandArgs(trailingOnly=TRUE)

result_file = "results.json"
if (length(args) > 0) result_file = args[1]

## load + munge data

res = result_file %>%
  as.tbl_json %>%
  gather_array %>%
  spread_values(test.name = jstring("name"), 
                language = jstring("language"),
                corpus_type = jstring("corpus_type"),
                model_index = jnumber("model_index")) %>%
  enter_object("results") %>%
  spread_values(test_stat = jnumber("test_stat"),
                pval = jnumber("pval"),
                effect_size = jnumber("effect_size")) %>%
  enter_object("words") %>%
  gather_array %>%
  spread_values(word = jstring("word"),
                word_set = jstring("word_set"),
                attr1_bias = jnumber("attr1_bias")) %>%
  data.table

res_all = result_file %>%
  as.tbl_json %>%
  gather_array %>%
  spread_values(test.name = jstring("name"), 
                language = jstring("language"),
                corpus_type = jstring("corpus_type"),
                model_index = jnumber("model_index")) %>%
  enter_object("results") %>%
  spread_values(test_stat = jnumber("test_stat"),
                pval = jnumber("pval"),
                effect_size = jnumber("effect_size")) %>%
  enter_object("words") %>%
  gather_array %>%
  data.table %>%
  `[`( , .N, 
       by=list(test.name, language, corpus_type, model_index, 
                     test_stat, pval, effect_size))

## prep for plotting

# TODO: align words with their lemma (e.g. 'primos'-'primo', 'Zuhause'-'zuhause') 
# to prevent vanishing segments in plot

res_all_avg = res_all %>%
  `[`(,
      list(avg_norm_WEAT=mean(test_stat/N),
           avg_pval=mean(pval),
           avg_effect_size=mean(effect_size)),
      by=list(language, test.name, corpus_type))

res_all_avg_seg = res_all_avg %>%
  dcast(language + test.name ~ corpus_type,
        value.var=c("avg_norm_WEAT", "avg_pval"))

res_word_avg = res %>%
  `[`( ,
       list(avg_male_bias=mean(attr1_bias/.N)),
       by=list(language, test.name, corpus_type, word, word_set))

res_word_avg_seg = res_word_avg %>%
  dcast(language + test.name + word + word_set ~ corpus_type,
        value.var=c("avg_male_bias"))

## reproduce plots + data

write.csv(res_all_avg, "results_summary.csv", row.names = FALSE)

ggsave("plot_overall.png",
  base_plot %+% res_all +
    aes(factor(paste(language, corpus_type),
               levels=c("de ", "de lemmatized",
                        "es ", "es lemmatized",
                        "nl ", "nl lemmatized",
                        "en ", "en lemmatized")), 
        abs(test_stat/N), col=language) +
    geom_point() +
    geom_point(data=res_all_avg,
               aes(y=abs(avg_norm_WEAT)),
               size=5, alpha=.4) +
    geom_segment(data=res_all_avg_seg,
                 aes(x=paste(language, ""),
                     xend=paste(language, "lemmatized"),
                     y=abs(avg_norm_WEAT_),
                     yend=abs(avg_norm_WEAT_lemmatized))) +
    facet_grid( ~ factor(test.name, levels=rev(sort(unique(test.name))))),
  width=8,
  height=4
)

tname = c("Topical career-family bias", "Grammatical gender masculine-feminine bias")
plot_suffix = c("topic", "gramm")

for (i in 1:2) {
  ggsave(paste0("plot_words_", plot_suffix[i], ".png"),
    base_plot %+% res_word_avg[test.name == tname[i]] +
      aes(corpus_type, avg_male_bias, color=word_set, label=word) +
      geom_blank() +
      geom_text(data=function(x) {x[corpus_type == ""]},
                hjust=1) + 
      geom_segment(data=res_word_avg_seg[test.name == tname[i]],
                   aes(x="",
                       xend="lemmatized",
                       y=V1,
                       yend=lemmatized)) +
      facet_grid(~ factor(language, levels=c("de", "es", "nl", "en"))) +
      ggtitle(tname[i]),
    scale=2,
    width=8
  )
}

