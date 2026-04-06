<!-- Source PDF: martinus-2019-masakhane.pdf -->

# A Focus on Neural Machine Translation for African Languages

Laura Martinus
Explore / Johannesburg, South Africa
laura@explore-ai.net
&Jade Abbott
Retro Rabbit / Johannesburg, South Africa
ja@retrorabbit.co.za

###### Abstract

African languages are numerous, complex and low-resourced. The datasets required for machine translation are difficult to discover, and existing research is hard to reproduce. Minimal attention has been given to machine translation for African languages so there is scant research regarding the problems that arise when using machine translation techniques. To begin addressing these problems, we trained models to translate English to five of the official South African languages (Afrikaans, isiZulu, Northern Sotho, Setswana, Xitsonga), making use of modern neural machine translation techniques. The results obtained show the promise of using neural machine translation techniques for African languages. By providing reproducible publicly-available data, code and results, this research aims to provide a starting point for other researchers in African machine translation to compare to and build upon.

## 1 Introduction

Africa has over 2000 languages across the continent *Eberhard et al. (2019)*. South Africa itself has 11 official languages. Unlike many major Western languages, the multitude of African languages are very low-resourced and the few resources that exist are often scattered and difficult to obtain.

Machine translation of African languages would not only enable the preservation of such languages, but also empower African citizens to contribute to and learn from global scientific, social and educational conversations, which are currently predominantly English-based *Alexander (2010)*. Tools, such as Google Translate *Google (2019)*, support a subset of the official South African languages, namely English, Afrikaans, isiZulu, isiXhosa and Southern Sotho, but do not translate the remaining six official languages.

Unfortunately, in addition to being low-resourced, progress in machine translation of African languages has suffered a number of problems. This paper discusses the problems and reviews existing machine translation research for African languages which demonstrate those problems. To try to solve the highlighted problems, we train models to perform machine translation of English to Afrikaans, isiZulu, Northern Sotho (N. Sotho), Setswana and Xitsonga, using state-of-the-art neural machine translation (NMT) architectures, namely, the Convolutional Sequence-to-Sequence (ConvS2S) and Transformer architectures.

Section 2 describes the problems facing machine translation for African languages, while the target languages are described in Section 3. Related work is presented in Section 4, and the methodology for training machine translation models is discussed in Section 5. Section 6 presents quantitative and qualitative results.

## 2 Problems

The difficulties hindering the progress of machine translation of African languages are discussed below.

Low availability of resources for African languages hinders the ability for researchers to do machine translation. Institutes such as the South African Centre for Digital Language Resources (SADiLaR) are attempting to change that by providing an open platform for technologies and resources for South African languages *Bergh (2019)*. This, however, only addresses the 11 official languages of South Africa and not the greater problems within Africa.

Discoverability: The resources for African languages that do exist are hard to find. Often one needs to be associated with a specific academic

|  Model | Afrikaans | isiZulu | N. Sotho | Setswana | Xitsonga  |
| --- | --- | --- | --- | --- | --- |
|  (Google, 2019) | 41.18 | 7.54 |  |  |   |
|  (Abbott and Martinus, 2018) |  |  |  | 33.53 |   |
|  (Wilken et al., 2012) |  |  |  | 28.8 |   |
|  (McKellar, 2014) |  |  |  |  | 37.31  |
|  (van Niekerk, 2014) | 71.0 | 7.9 | 37.9 |  | 40.3  |

Table 1: BLEU scores for English-to-Target language translation for related work.

institution in a specific country to gain access to the language data available for that country. This reduces the ability of countries and institutions to combine their knowledge and datasets to achieve better performance and innovations. Often the existing research itself is hard to discover since they are often published in smaller African conferences or journals, which are not electronically available nor indexed by research tools such as Google Scholar.

Reproducibility: The data and code of existing research are rarely shared, which means researchers cannot reproduce the results properly. Examples of papers that do not publicly provide their data and code are described in Section 4.

Focus: According to Alexander (2009), African society does not see hope for indigenous languages to be accepted as a more primary mode for communication. As a result, there are few efforts to fund and focus on translation of these languages, despite their potential impact.

Lack of benchmarks: Due to the low discoverability and the lack of research in the field, there are no publicly available benchmarks or leader boards to new compare machine translation techniques to.

This paper aims to address some of the above problems as follows: We trained models to translate English to Afrikaans, isiZulu, N. Sotho, Setswana and Xitsonga, using modern NMT techniques. We have published the code, datasets and results for the above experiments on GitHub, and in doing so promote reproducibility, ensure discoverability and create a baseline leader board for the five languages, to begin to address the lack of benchmarks.

## 3 Languages

We provide a brief description of the Southern African languages addressed in this paper, since many readers may not be familiar with them. The isiZulu, N. Sotho, Setswana, and Xitsonga languages belong to the Southern Bantu group of African languages (Mesthrie and Rajend, 2002).

The Bantu languages are agglutinative and all exhibit a rich noun class system, subject-verb-object word order, and tone (Zerbian, 2007). N. Sotho and Setswana are closely related and are highly mutually-intelligible. Xitsonga is a language of the Vatsonga people, originating in Mozambique (Bill, 1984). The language of isiZulu is the second most spoken language in Southern Africa, belongs to the Nguni language family, and is known for its morphological complexity (Keet and Khumalo, 2017; Bosch and Pretorius, 2017). Afrikaans is an analytic West-Germanic language, that descended from Dutch settlers (Roberge, 2002).

## 4 Related Work

This section details published research for machine translation for the South African languages. The existing research is technically incomparable to results published in this paper, because their datasets (in particular their test sets) are not published. Table 1 shows the BLEU scores provided by the existing work.

Google Translate (Google, 2019), as of February 2019, provides translations for English, Afrikaans, isiZulu, isiXhosa and Southern Sotho, six of the official South African languages. Google Translate was tested with the Afrikaans and isiZulu test sets used in this paper to determine its performance. However, due to the uncertainty regarding how Google Translate was trained, and which data it was trained on, there is a possibility that the system was trained on the test set used in this study as this test set was created from publicly available governmental data. For this reason, we determined this system is not comparable to this paper's models for isiZulu and Afrikaans.

Abbott and Martinus (2018) trained Transformer models for English to Setswana on the parallel Autshumato dataset (Groenewald and Fourie, 2009). Data was not cleaned nor was any additional data used. This is the only study reviewed that released datasets and code. Wilken et al. (2012) performed statistical phrase-based translation for English to Setswana translation. This re

|  Target Language | Afrikaans | isiZulu | N. Sotho | Setswana | Xitsonga  |
| --- | --- | --- | --- | --- | --- |
|  # Total Sentences | 53 172 | 26 728 | 30 777 | 123 868 | 193 587  |
|  # Training Sentences | 37 219 | 18 709 | 21 543 | 86 706 | 135 510  |
|  # Dev Sentences | 12 953 | 5 019 | 6 234 | 34 162 | 55 077  |
|  # Test Sentences | 3 000 | 3 000 | 3 000 | 3 000 | 3 000  |
|  # Tokens | 714 103 | 374 860 | 673 200 | 2 401 206 | 2 332 713  |
|  # Tokens (English) | 733 281 | 504 515 | 528 229 | 1 937 994 | 1 978 918  |

Table 2: Summary statistics for each dataset.

|  Source | Target | Back Translation | Issue  |
| --- | --- | --- | --- |
|  Note that the funds will be held against the Vote of the Provincial Treasury pending disbursement to the SMME Fund. | Lemali izohlala em-nyangweni wezimali. | The funds will be kept at the department of funds. | Translation does not match the source sentence at all.  |
|  Auctions | Ilungelo lomthengi lokwamukela ukuthi umphakeli unalo ilungelo lokuthengisa izimpahla | Consumer's right to accept that the supplier has the right to sell goods | Translation does not match the source sentence at all.  |
|  SERVICESTANDARDS | AMAQOHELO EMISEBENZI |  | A space between each letter in the source sentence.  |

Table 3: Examples of issues pertaining to the isizulu dataset.

search used linguistically-motivated pre- and post-processing of the corpus in order to improve the translations. The system was trained on the Autshumato dataset and also used an additional monolingual dataset.

McKellar (2014) used statistical machine translation for English to Xitsonga translation. The models were trained on the Autshumato data, as well as a large monolingual corpus. A factored machine translation system was used, making use of a combination of lemmas and part of speech tags.

van Niekerk (2014) used unsupervised word segmentation with phrase-based statistical machine translation models. These models translate from English to Afrikaans, N. Sotho, Xitsonga and isiZulu. The parallel corpora were created by crawling online sources and official government data and aligning these sentences using the HunAlign software package. Large monolingual datasets were also used.

Wolff and Kotze (2014) performed word translation for English to isiZulu. The translation system was trained on a combination of Autshumato, Bible, and data obtained from the South African Constitution. All of the isiZulu text was syllabified prior to the training of the word translation system.

It is evident that there is exceptionally little research available using machine translation techniques for Southern African languages. Only one of the mentioned studies provide code and datasets

for their results. As a result, the BLEU scores obtained in this paper are technically incomparable to those obtained in past papers.

## 5 Methodology

The following section describes the methodology used to train the machine translation models for each language. Section 5.1 describes the datasets used for training and their preparation, while the algorithms used are described in Section 5.2.

### 5.1 Data

The publicly-available Autshumato parallel corpora are aligned corpora of South African governmental data which were created for use in machine translation systems (Groenewald and Fourie, 2009). The datasets are available for download at the South African Centre for Digital Language Resources website. The datasets were created as part of the Autshumato project which aims to provide access to data to aid in the development of open-source translation systems in South Africa.

The Autshumato project provides parallel corpora for English to Afrikaans, isiZulu, N. Sotho, Setswana, and Xitsonga. These parallel corpora were aligned on the sentence level through a combination of automatic and manual alignment techniques.

The official Autshumato datasets contain many

duplicates, therefore to avoid data leakage between training, development and test sets, all duplicate sentences were removed. These clean datasets were then split into 70% for training, 30% for validation, and 3000 parallel sentences set aside for testing. Summary statistics for each dataset are shown in Table 2, highlighting how small each dataset is.

Even though the datasets were cleaned for duplicate sentences, further issues exist within the datasets which negatively affects models trained with this data. In particular, the isiZulu dataset is of low quality. Examples of issues found in the isiZulu dataset are explained in Table 3. The source and target sentences are provided from the dataset, the back translation from the target to the source sentence is given, and the issue pertaining to the translation is explained.

### 5.2 Algorithms

We trained translation models for two established NMT architectures for each language, namely, ConvS2S and Transformer. As the purpose of this work is to provide a baseline benchmark, we have not performed significant hyperparameter optimization, and have left that as future work.

The Fairseq(-py) toolkit was used to model the ConvS2S model *(Gehring et al., 2017)*. Fairseq’s named architecture “fconv” was used, with the default hyperparameters recommended by Fairseq documentation as follows: The learning rate was set to 0.25, a dropout of 0.2, and the maximum tokens for each mini-batch was set to 4000. The dataset was preprocessed using Fairseq’s preprocess script to build the vocabularies and to binarize the dataset. To decode the test data, beam search was used, with a beam width of 5. For each language, a model was trained using traditional white-space tokenisation, as well as byte-pair encoding tokenisation (BPE). To appropriately select the number of tokens for BPE, for each target language, we performed an ablation study (described in Section 6.3).

The Tensor2Tensor implementation of Transformer was used *(Vaswani et al., 2018)*. The models were trained on a Google TPU, using Tensor2Tensor’s recommended parameters for training, namely, a batch size of 2048, an Adafactor optimizer with learning rate warm-up of 10K steps, and a max sequence length of 64. The model was trained for 125K steps. Each dataset was encoded using the Tensor2Tensor data generation algorithm which invertibly encodes a native string as a sequence of subtokens, using WordPiece, an algorithm similar to BPE *(Kudo and Richardson, 2018)*. Beam search was used to decode the test data, with a beam width of 4.

## 6 Results

Section 6.1 describes the quantitative performance of the models by comparing BLEU scores, while a qualitative analysis is performed in Section 6.2 by analysing translated sentences as well as attention maps. Section 6.3 provides the results for an ablation study done regarding the effects of BPE.

### 6.1 Quantitative Results

The BLEU scores for each target language for both the ConvS2S and the Transformer models are reported in Table 4. For the ConvS2S model, we provide results for sentences tokenised by white spaces (Word), and when tokenised using the optimal number of BPE tokens (Best BPE), as determined in Section 6.3. The Transformer model uses the same number of WordPiece tokens as the number of BPE tokens which was deemed optimal during the BPE ablation study done on the ConvS2S model.

In general, the Transformer model outperformed the ConvS2S model for all of the languages, sometimes achieving 10 BLEU points or more over the ConvS2S models. The results also show that the translations using BPE tokenisation outperformed translations using standard word-based tokenisation. The relative performance of Transformer to ConvS2S models agrees with what has been seen in existing NMT literature *(Vaswani et al., 2017)*. This is also the case when using BPE tokenisation as compared to standard word-based tokenisation techniques *(Sennrich et al., 2015)*.

Overall, we notice that the performance of the NMT techniques on a specific target language is related to both the number of parallel sentences and the morphological typology of the language. In particular, isiZulu, N. Sotho, Setswana, and Xitsonga languages are all agglutinative languages, making them harder to translate, especially with very little data *(Chahuneau et al., 2013)*. Afrikaans is not agglutinative, thus despite having less than half the number of parallel sentences as Xit

|  Model | Afrikaans | isiZulu | N. Sotho | Setswana | Xitsonga  |
| --- | --- | --- | --- | --- | --- |
|  ConvS2S (Word) | 16.17 | 0.28 | 7.41 | 24.18 | 36.96  |
|  ConvS2S (Best BPE) | 25.04 (4k) | 1.79 (4k) | 12.18 (4k) | 26.36 (40k) | 37.45 (20k)  |
|  Transformer | 35.26 (4k) | 3.33 (4k) | 24.16 (4k) | 28.07 (40k) | 49.74 (20k)  |

Table 4: BLEU scores calculated for each model, for English-to-Target language translations on test sets.

songa and Setswana, the Transformer model still achieves reasonable performance. Xitsonga and Setswana are both agglutinative, but have significantly more data, so their models achieve much higher performance than N. Sotho or isizulu.

The translation models for isizulu achieved the worst performance when compared to the others, with the maximum BLEU score of 3.33. We attribute the bad performance to the morphological complexity of the language (as discussed in Section 3), the very small size of the dataset as well as the poor quality of the data (as discussed in Section 5.1).

### 6.2 Qualitative Results

We examine randomly sampled sentences from the test set for each language and translate them using the trained models. In order for readers to understand the accuracy of the translations, we provide back-translations of the generated translation to English. These back-translations were performed by a speaker of the specific target language. More examples of the translations are provided in the Appendix. Additionally, attention visualizations are provided for particular translations. The attention visualizations showed how the Transformer multi-head attention captured certain syntactic rules of the target languages.

#### 6.2.1 Afrikaans

In Table 5, ConvS2S did not perform the translation successfully. Despite the content being related to the topic of the original sentence, the semantics did not carry. On the other hand, Transformer achieved an accurate translation. Interestingly, the target sentence used an abbreviation, however, both translations did not. This is an example of how lazy target translations in the original dataset would negatively affect the BLEU score, and implore further improvement to the datasets. We plot an attention map to demonstrate the success of Transformer to learn the English-to-Afrikaans sentence structure in Figure 1.

#### 6.2.2 isizulu

Despite the bad performance of the English-to-isiZulu models, we wanted to understand how they were performing. The translated sentences, given in Table 6, do not make sense, but all of the words are valid isizulu words. Interestingly, the ConvS2S translation uses English words in the translation, perhaps due to English data occurring in the isizulu dataset. The ConvS2S however correctly prefixed the English phrase with the correct prefix "i-". The Transformer translation includes invalid acronyms and mentions "disease" which is not in the source sentence.

#### 6.2.3 Northern Sotho

If we examine Table 7, the ConvS2S model struggled to translate the sentence and had many repeating phrases. Given that the sentence provided is a difficult one to translate, this is not surprising. The Transformer model translated the sentence well, except included the word "boithabio", which in this context can be translated to "fun" - a concept that was not present in the original sentence.

#### 6.2.4 Setswana

Table 8 shows that the ConvS2S model translated the sentence very successfully. The word "khumo" directly means "wealth" or "riches". A better synonym would be "letseno", meaning income or "let-lotlo" which means monetary assets. The Transformer model only had a single misused word (translated "shortage" into "necessity"), but otherwise translated successfully. The attention map visualization in Figure 2 suggests that the attention mechanism has learnt that the sentence structure of Setswana is the same as English.

#### 6.2.5 Xitsonga

An examination of Table 9 shows that both models perform well translating the given sentence. However, the ConvS2S model had a slight semantic failure where the cause of the economic growth was attributed to unemployment, rather than vice versa.

![img-0000.jpeg](../img/martinus-2019-masakhane/img-0000.jpeg)

(a) Visualization of multi-head attention for Layer 1 for the word "cannot". The coloured bars are individual attention heads. The word "cannot" is translated to "kan nie ... nie" where the second negative "nie" occurs at the end of the sentence.

![img-0001.jpeg](../img/martinus-2019-masakhane/img-0001.jpeg)

(b) Visualization of multi-head attention for Layer 2 for the word "a". The coloured bars are individual attention heads. The word "a" is translated to "n", as is successfully captured by the attention mechanism.
Figure 1: Visualizations of multi-head attention for an English sentence translated to Afrikaans using the Transformer model.

Table 5: English to Afrikaans Translations: For the source sentence we show the reference translation, and the translations by the various models. We also show the translation of the results back to English, performed by an Afrikaans speaker.

|  Source | Identity documents are issued to South African citizens or permanent residence permit holders who are 16 years or older.  |
| --- | --- |
|  Target | ID's word uitgereik aan Suid-Afrikaanse burgers en persone wat 'n permanente verblyfpermit het en 16 jaar oud of ouer is.  |
|  ConvS2S | Identiteitsdokumente word uitgereik aan Suid-Afrikaanse burgers of permanente verblyfpermit wat 16 jaar of ouer is.  |
|  Back Translation | Identity documents are issued to South-African residents or permanent residence permits that are 16 years or older.  |
|  Transformer | Identiteitsdokumente word aan Suid-Afrikaanse burgers of permanente verblyfhouers wat 16 jaar of ouer is, uitgereik.  |
|  Back Translation | Identity documents are issued to South-African residents or permanent residence holders that are 16 years or older.  |

Table 6: English to isiZulu Translations: For the source sentence, we show the reference translation, and the translations by the various models. We also show the translation of the results back to English, performed by a isiZulu speaker.

|  Source | Note that the funds will be held against the Vote of the Provincial Treasury pending disbursement to the SMME Fund .  |
| --- | --- |
|  Target | Lemali izohlala emnyangweni wezimali .  |
|  ConvS2S | Qaphela ukuthi izimali izokhokhela i-Vote of the Provincial Treasury ngokuthengiswa kwabe-SMME .  |
|  Back Translation | Be aware the monies will pay the Vote of the Provincial Treasury with the paying by the SMME .  |
|  Transformer | Qaphela ukuthi izimali zizobanjwa kweVME esifundazweni saseTreasury zezifo ezithunyelwa ku-MSE .  |
|  Back Translation | Be aware that the money will be held by VME with facilities of Treasury with diseases sent to MSE .  |

Table 7: English to Northern Sotho Translations: For the source sentence we show the reference translation, and the translations by the various models. We also show the translation of the results back to English, performed by a Northern Sotho speaker.

|  Source | No fishing vessel will be registered without a fishing right and a permit to engage in fishing activities.  |
| --- | --- |
|  Target | Ga go sekepe sa go rea dihlapi seo se tla go retisetarwa/ngwadiwa ka ntle ga go ba le tokelo ya go rea dihlapi le tumelelo ya go kgatha tema mererong wa go rea dihlapi.  |
|  ConvS2S | Ga go phemiti ya go rea dihlapi e tla ngwadiwa ka ntle le phemiti ya go rea dihlapi le phemiti ya go rea dihlapi.  |
|  Back Translation | There is no permit for fishing that can be registered for without a permit for fishing and a permit for fishing.  |
|  Transformer | Ga go sekepe sa go rea dihlapi seo se tla go ngwadiwa tokelo ya go rea dihlapi le tumelelo ya go rea dihlapi ka mabaka a boithabio.  |
|  Back Translation | There is no fishing boat that will give you the right to fish and permission to fish for fun.  |

Table 8: English to Setswana Translations: For the source sentence we show the reference translation, and the translations by the various models. We also show the translation of the results back to English, performed by a Setswana speaker.

|  Source | If there is a shortage of bees in the sunflower lands during the flowering period it may lead to a possible loss of production by 25% .  |
| --- | --- |
|  Target | Fa palo ya dinotshe e le kwa tase mo masimong a disonobolomo ka nako ya go thuntsha dithunya go ka tisa phokotso ya kumo e e ka nnang 25% .  |
|  ConvS2S | Fa go na le tlhaelo ya dinotshe mo masimong a sonobolomo ka nako ya go thunya dithunya go ka tlietsa tathlegelo ya kumo ka 25%  |
|  Back Translation | If there is a shortage of bees in the sunflower fields during the blooming season this can bring about a loss of income by 25%  |
|  Transformer | Fa go na le botlhokwa ba dinotshe mo masimong a disonobolomo fa nako ya go supa dithunya e ka simolola go thunya go ka fokotsa tathlego ya kumo ka 25% .  |
|  Back Translation | If there is a need/importance/necessity/requirement/relevance for bees in the sunflower farms/fields when the blossoming season begins this can reduce loss of income by 25%  |

Table 9: English to Xitsonga Translations: For the source sentence we show the reference translation, and the translations by the various models. We also show the translation of the results back to English, performed by a Xitsonga speaker.

|  Source | we are concerned that unemployment and poverty persist despite the economic growth experienced in the past 10 years .  |
| --- | --- |
|  Target | hi na swivilelo leswaku mpfumaleko wa mitirho na vusweti swi ya emahlweni hambileswi ku nga va na ku kula ka ikhonomi eka malembe ya 10 lawa ya hundzeke .  |
|  ConvS2S | hi vilela leswaku ku pfumaleka ka mitirho na vusweti swi papalata ku kula ka ikhonomi eka malembe ya 10 lama nga hundza .  |
|  Back Translation | We are concerned that the lack of jobs and poverty has prevented economic growth in the past 10 years.  |
|  Transformer | hi na swivilelo leswaku mpfumaleko wa mitirho na vusweti swi ya emahlweni hambileswi ku nga va na ku kula ka ikhonomi eka malembe ya 10 lawa ya hundzeke .  |
|  Back Translation | We have concerns that there is still lack of jobs and poverty even though there has been economic growth in the past 10 years.  |

![img-0002.jpeg](../img/martinus-2019-masakhane/img-0002.jpeg)

Figure 2: Visualization of multi-head attention for Layer 5 for the word "concerned". "Concerned" translates to "tshwenyegile" while "gore" is a connecting word like "that".

### 6.3 Ablation Study over the Number of Tokens for Byte-pair Encoding

BPE (Sennrich et al., 2015) and its variants, such as SentencePiece (Kudo and Richardson, 2018), aid translation of rare words in NMT systems. However, the choice of the number of tokens to generate for any particular language is not made obvious by literature. Popular choices for the number of tokens are between 30,000 and 40,000: Vaswani et al. (2017) use 37,000 for WMT 2014 English-to-German translation task and 32,000 tokens for the WMT 2014 English-to-French translation task. Johnson et al. (2017) used 32,000 SentencePiece tokens across all source and target data. Unfortunately, no motivation for the choice for the number of tokens used when creating sub-words has been provided.

Initial experimentation suggested that the choice of the number of tokens used when running BPE tokenisation, affected the model's final performance significantly. In order to obtain the best results for the given datasets and models, we performed an ablation study, using subword-nmt

(Sennrich et al., 2015), over the number of tokens required by BPE, for each language, on the ConvS2S model. The results of the ablation study are shown in Figure 3.

![img-0003.jpeg](../img/martinus-2019-masakhane/img-0003.jpeg)

Figure 3: The BLEU scores for the ConvS2S of each target language w.r.t the number of BPE tokens.

As can be seen in Figure 3, the models for languages with the smallest datasets (namely isiZulu and N. Sotho) achieve higher BLEU scores when the number of BPE tokens is smaller, and decrease as the number of BPE tokens increases. In contrast, the performance of the models for languages with larger datasets (namely Setswana, Xitsonga, and Afrikaans) improves as the number of BPE tokens increases. There is a decrease in performance at 20 000 BPE tokens for Setswana and Afrikaans, which the authors cannot yet explain and require further investigation. The optimal number of BPE tokens were used for each language, as indicated in Table 4.

## 7 Future Work

Future work involves improving the current datasets, specifically the isiZulu dataset, and thus improving the performance of the current machine translation models.

As this paper only provides translation models for English to five of the South African languages and Google Translate provides translation for an additional two languages, further work needs to be done to provide translation for all 11 official languages. This would require performing data collection and incorporating unsupervised (Lample et al., 2018; Lample and Conneau, 2019), meta-learning (Gu et al., 2018), or zero-shot techniques (Johnson et al., 2017).

8 Conclusion

African languages are numerous and low-resourced. Existing datasets and research for machine translation are difficult to discover, and the research hard to reproduce. Additionally, very little attention has been given to the African languages so no benchmarks or leader boards exist, and few attempts at using popular NMT techniques exist for translating African languages.

This paper reviewed existing research in machine translation for South African languages and highlighted their problems of discoverability and reproducibility. In order to begin addressing these problems, we trained models to translate English to five South African languages, using modern NMT techniques, namely ConvS2S and Transformer. The results were promising for the languages that have more higher quality data (Xitsonga, Setswana, Afrikaans), while there is still extensive work to be done for isiZulu and N. Sotho which have exceptionally little data and the data is of worse quality. Additionally, an ablation study over the number of BPE tokens was performed for each language. Given that all data and code for the experiments are published on GitHub, these benchmarks provide a starting point for other researchers to find, compare and build upon.

The source code and the data used are available at https://github.com/LauraMartinus/ukuxhumana.

## Acknowledgements

The authors would like to thank Reinhard Cromhout, Guy Bosa, Mbongiseni Ncube, Seale Rapolai, and Vongani Maluleke for assisting us with the back-translations, and Jason Webster for Google Translate API assistance. Research supported with Cloud TPUs from Google’s TensorFlow Research Cloud (TFRC).

## References

- Abbott and Martinus [2018] Jade Z Abbott and Laura Martinus. 2018. Towards neural machine translation for African languages. arXiv preprint arXiv:1811.05467.
- Alexander [2009] Neville Alexander. 2009. Evolving African approaches to the management of linguistic diversity: The ACALAN project. Language Matters, 40(2):117–132.
- Alexander [2010] Neville Alexander. 2010. The potential role of translation as social practice for the intellectualisation of African languages. PRAESA Cape Town.
- Alana [1984] Liané van den Bergh. 2019. Sadilar. https://www.sadilar.org/.
- Bosc [1983] Mary C. Bill. 1984. 100 years of Tsonga publications, 18831983. African Studies, 43(2):67–81.
- Belin et al. [2017] Sonja E. Bosch and Laurette Pretorius. 2017. A Computational Approach to Zulu Verb Morphology within the Context of Lexical Semantics. Lexikos, 27:152 – 182.
- Chahuneau et al. [2013] Victor Chahuneau, Eva Schlinger, Noah A Smith, and Chris Dyer. 2013. Translating into morphologically rich languages with synthetic phrases. In Proceedings of the 2013 Conference on Empirical Methods in Natural Language Processing, pages 1677–1687.
- Eberhard et al. [2019] David M Eberhard, Gary F. Simons, and Charles D. Fennig. 2019. Ethnologue: Languages of the worlds. twenty-second edition.
- Gehring et al. [2017] Jonas Gehring, Michael Auli, David Grangier, Denis Yarats, and Yann N Dauphin. 2017. Convolutional sequence to sequence learning. arXiv preprint arXiv:1705.03122.
- Gogle [2019] Google. 2019. Google translate. https://translate.google.co.za/. Accessed: 2019-02-19.
- Hende et al. [2009] Hendrik J Groenewald and Wildrich Fourie. 2009. Introducing the Autshumato integrated translation environment. In Proceedings of the 13th Annual Conference of the EAMT, Barcelona, May, pages 190–196. Citeseer.
- Gu et al. [2018] Jiatao Gu, Yong Wang, Yun Chen, Kyunghyun Cho, and Victor OK Li. 2018. Meta-learning for low-resource neural machine translation. arXiv preprint arXiv:1808.08437.
- Johnson et al. [2017] Melvin Johnson, Mike Schuster, Quoc V Le, Maxim Krikun, Yonghui Wu, Zhifeng Chen, Nikhil Thorat, Fernanda Viégas, Martin Wattenberg, Greg Corrado, et al. 2017. Googles multilingual neural machine translation system: Enabling zero-shot translation. Transactions of the Association for Computational Linguistics, 5:339–351.
- Kett and Khumalo [2017] C Maria Keet and Langa Khumalo. 2017. Grammar rules for the isizulu complex verb. Southern African Linguistics and Applied Language Studies, 35(2):183–200.
- Kudo and Richardson [2018] Taku Kudo and John Richardson. 2018. Sentencepiece: A simple and language independent subword tokenizer and detokenizer for neural text processing. arXiv preprint arXiv:1808.06226.
- Lamey and Combes [2019] Guillaume Lamey and Alexis Conneau. 2019. Crosslingual language model pretraining. arXiv preprint arXiv:1901.07291.
- Lamey and Combes [2018] Guillaume Lamey, Alexis Conneau, Ludovic Denoyer, and Marc’Aurelio Ranzato. 2018. Unsupervised machine translation using monolingual corpora only. In International Conference on Learning Representations (ICLR).

Cindy A. McKellar. 2014. An English to Xitsonga statistical machine translation system for the government domain. In Proceedings of the 2014 PRASA, RobMech and AfLaT International Joint Symposium, pages 229–233.

Rajend Mesthrie and Mesthrie Rajend. 2002. Language in South Africa. Cambridge University Press.

Daniel R van Niekerk. 2014. Exploring unsupervised word segmentation for machine translation in the South African context. In Proceedings of the 2014 PRASA, RobMech and AfLaT International Joint Symposium, pages 202–206.

Paul T Roberge. 2002. Afrikaans: considering origins. Language in South Africa, pages 79–103.

Rico Sennrich, Barry Haddow, and Alexandra Birch. 2015. Neural machine translation of rare words with subword units. arXiv preprint arXiv:1508.07909.

Ashish Vaswani, Samy Bengio, Eugene Brevdo, Francois Chollet, Aidan N. Gomez, Stephan Gouws, Llion Jones, Łukasz Kaiser, Nal Kalchbrenner, Niki Parmar, Ryan Sepassi, Noam Shazeer, and Jakob Uszkoreit. 2018. Tensor2tensor for neural machine translation. CoRR, abs/1803.07416.

Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, and Illia Polosukhin. 2017. Attention is all you need. CoRR, abs/1706.03762.

Ilana Wilken, Marissa Griesel, and Cindy McKellar. 2012. Developing and improving a statistical machine translation system for English to Setswana: a linguistically-motivated approach. In Twenty-Third Annual Symposium of the Pattern Recognition Association of South Africa, page 114.

Friedel Wolff and Gideon Kotze. 2014. Experiments with syllable-based Zulu-English machine translation. In Proceedings of the 2014 PRASA, RobMech and AfLaT International Joint Symposium, pages 217–222.

Sabine Zerbian. 2007. A first approach to information structuring in Xitsonga/Xichangana. Research in African Languages and Linguistics, 7(2005-2006):1–22.

# A Appendix

Additional translation results from ConvS2S and Transformer are given in Table 10 along with their back-translations for Afrikaans, N. Sotho, Setswana, and Xitsonga. We include these additional sentences as we feel that the single sentence provided per language in Section 6.2, is not enough demonstrate the capabilities of the models. Given the scarcity of research in this field, researchers might find the additional sentences insightful into understanding the real-world capabilities and potential, even if BLEU scores are low.

Table 10: For each source sentence we show the reference translation, and the translations by the various models. We also show the translation of the results back to English, performed by a home-language speaker.

|  Source Afrikaans | If you want to work as a tourist guide in the Western Cape, you need to be registered with the provincial Tourist Guide Office.  |
| --- | --- |
|  Target | As jy in die Wes-Kaap wil werk as 'n toergids, moet jy geregistreer wees by die provinsiale Toergidskantoor.  |
|  ConvS2S | As jy wil werk as 'n toergids in die Wes-Kaap, moet jy by die provinsiale Toeristeids geregistreer wees.  |
|  Back Translation | If you want to work as a tour guide in the Western Cape, you have to be registered at the provincial <UNK>.  |
|  Transformer | As jy wil werk as 'n toergids in die Wes-Kaap wil werk, moet jy geregistreer wees by die provinsiale Toergids kantoor.  |
|  Back Translation | If you want to work as a tour guide in the Western Cape want to work, you have to be registered at the provincial Tour guide office.  |
|  Source N. Sotho | A veterinary import permit is needed to import animals or animal products into the Republic of South Africa.  |
|  Target | Tumelelo ya thekontle ya diphoofolo go di tliwa ka nageng e a hlokagala go reka diphoofolo le ditweletwa ta diphoofolo ka ntle go tlia ka mo Repabliking ya Afrika Borwa.  |
|  ConvS2S | Tumelelo ya thekontle ya diphoofolo e a nyakega go reka diphoofolo ta diphoofolo goba ditweletwa ta diphoofolo ka ntle ga Afrika Borwa.  |
|  Back Translation | Permission to import animals is needed to buy animals for animals products animals outside of South Africa.  |
|  Transformer | Tumelelo ya thekontle ya diphoofolo go di tliwa ka nageng e a hlokagala go reka diphoofolo le ditweletwa ta diphoofolo ka ntle go tlia ka mo Repabliking ya Afrika Borwa.  |
|  Back Translation | Permission to import animals from outside the country is needed to buy animals and products for animals without bringing them into the Republic of South Africa.  |
|  Source Setswana | Councillors, together with officials, must ensure that there is enough money to deliver services and promote the planned development.  |
|  Target | Bakhanselara mmogo le baofisiri, ba tshwanetse go netefatsa gore go na le thelete e e lekaneng go rebola ditirelo le go tsweletsa tlhabololo e e rulagantsweng.  |
|  ConvS2S | Bakhanselara, mmogo le batlhankedi, ba tshwanetse go netefatsa gore go na le madi a a lekaneng a go rebola ditirelo le go rotloetsa tlhabololo e e rulagantsweng.  |
|  Back Translation | Counselors, together with <UNK>, must ensure there is enough money to permit continuous services and to encourage development as planned.  |
|  Transformer | Bakhanselara mmogo le batlhankedi, ba tshwanetse go netefatsa gore go na le madi a a lekaneng go rebola ditirelo le go tsweletsa tlhabololo e e rulagantsweng.  |
|  Back Translation | Counselors together with <UNK>, are supposed to ensure that there's enough funds to permit services and to continue development as planned.  |
|  Source Xitsonga | Improvement of performance in the public service also depends on the quality of leadership provided by the executive and senior management.  |
|  Target | Ku antswisa matirhelo eka mfumo swi tlhela swi ya hi nkoka wa vurhangeri lowu nyikiwaka hi vulawuri na vufambisi nkulu.  |
|  ConvS2S | Ku antswisiwa ka matirhelo eka mitirho ya mfumo swi tlhela swi ya hi nkoka wa vurhangeri lebyi nyikiwaka hi vufambisi na mafambiselo ya xiyimo xa le henhla.  |
|  Back Translation | The improvement of the governments work depends on the quality of the leadership which is provided by the management and the best system implemented.  |
|  Transformer | Ku antswisiwa ka matirhelo eka vukorhokeri bya mfumo na swona swi ya hi nkoka wa vurhangeri lebyi nyikiwaka hi komitinkulu na mafambiselo ya le henhla.  |
|  Back Translation | The improvement of service delivery by the government also depends on the quality of leadership which is provided by the high committee and the best implemented system.  |