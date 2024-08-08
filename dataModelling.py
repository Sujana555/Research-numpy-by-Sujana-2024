import csv
import nltk
import numpy as np
import json
import glob
from gensim.models import TfidfModel

# Gensim
import gensim
import gensim.corpora as corpora
from gensim.utils import simple_preprocess
from gensim.models import CoherenceModel

# SpaCy
import spacy
from nltk.corpus import stopwords

# Visualization
import pyLDAvis
import pyLDAvis.gensim

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Preparing the Data
def load_data(file):
    with open(file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]
    return data

def write_data(file, data):
    with open(file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

stopwords = stopwords.words("english")
print(stopwords)

csv_file_path = "updated.csv"

data = load_data(csv_file_path)

def lemmatization(texts, allowed_postags=["NOUN", "ADJ", "VERB", "ADV"]):
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    texts_out = []

    for text in texts:
        doc = nlp(text)
        new_text = []

        for token in doc:
            if token.pos_ in allowed_postags:
                new_text.append(token.lemma_)

        final = " ".join(new_text)
        texts_out.append(final)

    return texts_out

data_in_texts = [item["questionBody"] for item in data]

print("Before", data_in_texts[0][0:90])
lemmatized_texts = lemmatization(data_in_texts, allowed_postags=["NOUN", "ADJ", "VERB", "ADV"])
print("After:", lemmatized_texts[0][0:90])

def gen_words(texts):
    final = []
    for text in texts:
        new = gensim.utils.simple_preprocess(text, deacc=True)
        final.append(new)
    return final

data_words = gen_words(lemmatized_texts)

print(data_words[0][0:20])

# Bigrams and trigrams
bigrams_phrases = gensim.models.Phrases(data_words, min_count=5, threshold=50)
trigram_phrases = gensim.models.Phrases(bigrams_phrases[data_words], threshold=50)

bigram = gensim.models.phrases.Phraser(bigrams_phrases)
trigram = gensim.models.phrases.Phraser(trigram_phrases)

def make_bigrams(texts):
    return (bigram[doc] for doc in texts)

def make_trigram(texts):
    return (trigram[bigram[doc]] for doc in texts)

data_bigrams = make_bigrams(data_words)
data_bigrams_trigrams = make_trigram(data_bigrams)

# Convert generators to lists
data_bigrams_trigrams = list(data_bigrams_trigrams)

print(data_bigrams_trigrams[0])

# TF-IDF removal
id2word = corpora.Dictionary(data_bigrams_trigrams)

texts = data_bigrams_trigrams

corpus = [id2word.doc2bow(text) for text in texts]

tfidf = TfidfModel(corpus, id2word=id2word)

low_value = 0.03
words = []
words_missing_in_tfidf = []

for i in range(0, len(corpus)):
    bow = corpus[i]
    low_value_words = []
    tfidf_ids = [id for id, value in tfidf[bow]]
    bow_ids = [id for id, value in tfidf[bow] if value < low_value]
    drops = low_value_words + words_missing_in_tfidf
    for item in drops:
        words.append(id2word[item])
    words_missing_in_tfidf = [id for id in bow_ids if id not in tfidf_ids]

    new_bow = [b for b in bow if b[0] not in low_value_words and b[0] not in words_missing_in_tfidf]
    corpus[i] = new_bow

lda_model = gensim.models.LdaModel(corpus=corpus,
                                   id2word=id2word,
                                   num_topics=30,
                                   random_state=100,
                                   update_every=1,
                                   chunksize=100,
                                   passes=10,
                                   alpha="auto")

# LDA visualization using pyLDAvis
vis = pyLDAvis.gensim.prepare(lda_model, corpus, id2word, mds="nmds", R=30)
pyLDAvis.save_html(vis, 'lda_visualization.html')

# Confirmation message
print("LDA visualization saved as lda_visualization.html")

# --- Add the following section to save questions by topic ---

# Get the topic distribution for each question
topic_assignments = lda_model.get_document_topics(corpus, minimum_probability=0)

# Create a list to store the most dominant topic for each question
dominant_topics = []

for i, topics in enumerate(topic_assignments):
    # Sort topics by probability and get the most likely topic
    sorted_topics = sorted(topics, key=lambda x: x[1], reverse=True)
    dominant_topic = sorted_topics[0][0]  # Get the topic number
    dominant_topics.append(dominant_topic)

# Add this dominant topic information back to the original data
for i, item in enumerate(data):
    item['dominant_topic'] = dominant_topics[i]

# Create a dictionary to hold questions by topic
questions_by_topic = {topic: [] for topic in range(lda_model.num_topics)}

# Group questions by their dominant topic
for item in data:
    topic = item['dominant_topic']
    questions_by_topic[topic].append(item)

# Save each topic's questions to a separate CSV file
for topic, questions in questions_by_topic.items():
    if questions:  # Check if the list is not empty
        file_name = f'Topic_{topic}_questions.csv'
        write_data(file_name, questions)
        print(f"Saved {len(questions)} questions to {file_name}.")
    else:
        print(f"No questions found for topic {topic}.")














# import csv
# import nltk
# import numpy as np
# import json
# import glob
# from gensim.models import TfidfModel
#
# # Gensim
# import gensim
# import gensim.corpora as corpora
# from gensim.utils import simple_preprocess
# from gensim.models import CoherenceModel
#
# # SpaCy
# import spacy
# from nltk.corpus import stopwords
#
# # Visualization
# import pyLDAvis
# import pyLDAvis.gensim
#
# import warnings
# warnings.filterwarnings("ignore", category=DeprecationWarning)
#
# # Preparing the Data
# def load_data(file):
#     with open(file, mode='r', encoding='utf-8') as f:
#         reader = csv.DictReader(f)
#         data = [row for row in reader]
#     return data
#
# def write_data(file, data):
#     with open(file, mode='w', newline='', encoding='utf-8') as f:
#         writer = csv.DictWriter(f, fieldnames=data[0].keys())
#         writer.writeheader()
#         writer.writerows(data)
#
# stopwords = stopwords.words("english")
# print(stopwords)
#
# csv_file_path = "updated.csv"
#
# data = load_data(csv_file_path)
#
# def lemmatization(texts, allowed_postags=["NOUN", "ADJ", "VERB", "ADV"]):
#     nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
#     texts_out = []
#
#     for text in texts:
#         doc = nlp(text)
#         new_text = []
#
#         for token in doc:
#             if token.pos_ in allowed_postags:
#                 new_text.append(token.lemma_)
#
#         final = " ".join(new_text)
#         texts_out.append(final)
#
#     return texts_out
#
# data_in_texts = [item["questionBody"] for item in data]
#
# print("Before", data_in_texts[0][0:90])
# lemmatized_texts = lemmatization(data_in_texts, allowed_postags=["NOUN", "ADJ", "VERB", "ADV"])
# print("After:", lemmatized_texts[0][0:90])
#
# def gen_words(texts):
#     final = []
#     for text in texts:
#         new = gensim.utils.simple_preprocess(text, deacc=True)
#         final.append(new)
#     return final
#
# data_words = gen_words(lemmatized_texts)
#
# print(data_words[0][0:20])
#
# # Bigrams and trigrams
# bigrams_phrases = gensim.models.Phrases(data_words, min_count=5, threshold=50)
# trigram_phrases = gensim.models.Phrases(bigrams_phrases[data_words], threshold=50)
#
# bigram = gensim.models.phrases.Phraser(bigrams_phrases)
# trigram = gensim.models.phrases.Phraser(trigram_phrases)
#
# def make_bigrams(texts):
#     return (bigram[doc] for doc in texts)
#
# def make_trigram(texts):
#     return (trigram[bigram[doc]] for doc in texts)
#
# data_bigrams = make_bigrams(data_words)
# data_bigrams_trigrams = make_trigram(data_bigrams)
#
# # Convert generators to lists
# data_bigrams_trigrams = list(data_bigrams_trigrams)
#
# print(data_bigrams_trigrams[0])
#
# # TF-IDF removal
# id2word = corpora.Dictionary(data_bigrams_trigrams)
#
# texts = data_bigrams_trigrams
#
# corpus = [id2word.doc2bow(text) for text in texts]
#
# tfidf = TfidfModel(corpus, id2word=id2word)
#
# low_value = 0.03
# words = []
# words_missing_in_tfidf = []
#
# for i in range(0, len(corpus)):
#     bow = corpus[i]
#     low_value_words = []
#     tfidf_ids = [id for id, value in tfidf[bow]]
#     bow_ids = [id for id, value in tfidf[bow] if value < low_value]
#     drops = low_value_words + words_missing_in_tfidf
#     for item in drops:
#         words.append(id2word[item])
#     words_missing_in_tfidf = [id for id in bow_ids if id not in tfidf_ids]
#
#     new_bow = [b for b in bow if b[0] not in low_value_words and b[0] not in words_missing_in_tfidf]
#     corpus[i] = new_bow
#
# lda_model = gensim.models.LdaModel(corpus=corpus,
#                                    id2word=id2word,
#                                    num_topics=30,
#                                    random_state=100,
#                                    update_every=1,
#                                    chunksize=100,
#                                    passes=10,
#                                    alpha="auto")
#
# vis = pyLDAvis.gensim.prepare(lda_model, corpus, id2word, mds="nmds", R=30)
# pyLDAvis.save_html(vis, 'lda_visualization.html')
#
# # Confirmation message
# print("LDA visualization saved as lda_visualization.html")
