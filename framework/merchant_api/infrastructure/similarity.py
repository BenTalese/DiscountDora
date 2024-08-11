from fuzzywuzzy import fuzz


def get_similarity_score(phrase_to_score: str, phrase_to_match: str, similarity_threshold: int) -> int:
    _String1Words = phrase_to_score.lower().split()
    _String2Words = phrase_to_match.lower().split()
    _Score = 0

    _MatchedWords = set()
    for _Word1 in _String1Words:
        for _Word2 in _String2Words:
            _Similarity = fuzz.ratio(_Word1, _Word2)
            if _Similarity >= similarity_threshold and _Word2 not in _MatchedWords:
                _Score += _Similarity
                _MatchedWords.add(_Word2)

    return _Score


def get_min_similarity_score(phrase: str, similarity_threshold: int) -> int:
    return len(phrase.lower().split()) * similarity_threshold


def is_similar_phrase(comparison_phrase, phrase_to_match: str, similarity_threshold: int) -> bool:
    _SimilarityScore = get_similarity_score(comparison_phrase, phrase_to_match, similarity_threshold)
    _MinSimilarity = get_min_similarity_score(phrase_to_match, similarity_threshold)

    return _SimilarityScore >= _MinSimilarity
