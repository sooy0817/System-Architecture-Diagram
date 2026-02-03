# app/core/candidates.py
from app.extract.candidate_extractor import CandidateExtractor

_ce = None


def get_candidate_extractor() -> CandidateExtractor:
    global _ce
    if _ce is None:
        _ce = CandidateExtractor()
    return _ce
