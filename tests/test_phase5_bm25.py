from pathlib import Path

import numpy as np

from devoteam_reference_ai.phase5_bm25 import (
    BM25Index,
    normalize_search_text,
    tokenize_multilingual,
)


def test_multilingual_normalization_handles_accents_and_arabic_variants():
    assert normalize_search_text("ÉTUDES") == "etudes"
    assert tokenize_multilingual("L’étude numérique") == ["etude", "numerique"]
    assert tokenize_multilingual("إدارةُ الأعمال") == ["ادارة", "الاعمال"]


def test_bm25_ranks_exact_domain_terms_first():
    index = BM25Index.build(
        [
            "schéma directeur système information banque",
            "audit cybersécurité réseau télécom",
            "gestion de projet secteur public",
        ]
    )
    scores = index.score("cybersécurité télécom")
    assert int(np.argmax(scores)) == 1
    index.verify()


def test_bm25_round_trip_without_pickle(tmp_path: Path):
    source = BM25Index.build(["banque tunisie", "assurance maroc", "banque maroc"])
    index_path = tmp_path / "index.npz"
    vocabulary_path = tmp_path / "vocabulary.json"
    source.save(index_path, vocabulary_path)
    loaded = BM25Index.load(index_path, vocabulary_path)
    assert loaded.vocabulary == source.vocabulary
    np.testing.assert_allclose(loaded.score("banque maroc"), source.score("banque maroc"))


def test_bm25_security_mask_excludes_unauthorized_rows():
    index = BM25Index.build(["banque", "banque", "banque"])
    scores = index.score("banque", allowed_mask=np.asarray([True, False, True]))
    assert np.isneginf(scores[1])
    assert np.isfinite(scores[[0, 2]]).all()
