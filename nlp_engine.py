# nlp_engine.py - advanced NLP
import spacy
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from textblob import TextBlob

try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

def extract_entities(text):
    if not nlp:
        return []
    doc = nlp(text[:100000])
    return [(ent.text, ent.label_) for ent in doc.ents]

def sentiment(text):
    blob = TextBlob(text)
    return {"polarity": blob.sentiment.polarity, "subjectivity": blob.sentiment.subjectivity}

def keywords_tfidf(text, top_n=15):
    vec = TfidfVectorizer(stop_words="english", max_features=100)
    X = vec.fit_transform([text])
    scores = zip(vec.get_feature_names_out(), X.toarray()[0])
    return sorted(scores, key=lambda x: x[1], reverse=True)[:top_n]

def topic_model(docs, n_topics=3):
    if len(docs) < 2:
        return []
    vec = CountVectorizer(stop_words="english", max_df=0.9, min_df=1)
    X = vec.fit_transform(docs)
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(X)
    topics = []
    words = vec.get_feature_names_out()
    for topic_idx, topic in enumerate(lda.components_):
        top = [words[i] for i in topic.argsort()[-7:][::-1]]
        topics.append(top)
    return topics

def extract_job_keywords(job_description):
    ents = extract_entities(job_description)
    skills = [e[0] for e in ents if e[1] in ("ORG", "PRODUCT", "SKILL", "WORK_OF_ART")]
    tfidf = [w for w, s in keywords_tfidf(job_description)]
    # combine
    combined = list(dict.fromkeys(skills + tfidf))[:25]
    return combined
