"""
02_preprocessing.py
Lab 5 minimal_clean profile: lowercase + URL removal + whitespace normalization.

Deliberately does NOT stem/lemmatize, strip stopwords, or delete numbers, because
dosages, hour counts ("24 hours", "48hours") and drug names are exactly the kind of
information Lab 5 warned not to throw away. Semantic embeddings are fed raw text;
only the lexical retrievers (TF-IDF / BM25) use this light cleaning.
"""

import re


def remove_urls(text):
    return re.sub(r"http\S+|www\.\S+", "", text)


def normalize_whitespace(text):
    return re.sub(r"\s+", " ", text).strip()


def preprocess_text(text, lowercase=True, remove_url=True, normalize_space=True):
    if lowercase:
        text = text.lower()
    if remove_url:
        text = remove_urls(text)
    if normalize_space:
        text = normalize_whitespace(text)
    return text


if __name__ == "__main__":
    sample = "  Rinse with WARM salt water   a few times daily.  See www.clinic.com  "
    print("RAW  :", repr(sample))
    print("CLEAN:", repr(preprocess_text(sample)))
