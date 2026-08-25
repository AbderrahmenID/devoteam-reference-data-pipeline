from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
ARABIC_DIACRITICS_RE = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")


def normalize_search_text(value: object) -> str:
    """Normalize French, English, and Arabic text without language-specific stemming."""
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = ARABIC_DIACRITICS_RE.sub("", text).replace("ـ", "")
    text = text.translate(
        str.maketrans(
            {
                "أ": "ا",
                "إ": "ا",
                "آ": "ا",
                "ٱ": "ا",
                "ى": "ي",
                "ؤ": "و",
                "ئ": "ي",
            }
        )
    )
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def tokenize_multilingual(value: object) -> list[str]:
    return [token for token in TOKEN_RE.findall(normalize_search_text(value)) if len(token) >= 2]


@dataclass
class BM25Index:
    vocabulary: list[str]
    offsets: np.ndarray
    posting_rows: np.ndarray
    term_frequencies: np.ndarray
    idf: np.ndarray
    document_lengths: np.ndarray
    average_document_length: float
    k1: float = 1.2
    b: float = 0.75

    @property
    def document_count(self) -> int:
        return int(len(self.document_lengths))

    @classmethod
    def build(cls, texts: Iterable[str], *, k1: float = 1.2, b: float = 0.75) -> "BM25Index":
        tokenized = [tokenize_multilingual(text) for text in texts]
        if not tokenized:
            raise ValueError("BM25 corpus may not be empty")
        lengths = np.asarray([len(tokens) for tokens in tokenized], dtype=np.float32)
        if not np.all(lengths > 0):
            raise ValueError("BM25 corpus contains an empty token sequence")
        postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for row_index, tokens in enumerate(tokenized):
            for token, frequency in Counter(tokens).items():
                postings[token].append((row_index, frequency))
        vocabulary = sorted(postings)
        offsets = [0]
        posting_rows: list[int] = []
        term_frequencies: list[float] = []
        idf: list[float] = []
        document_count = len(tokenized)
        for token in vocabulary:
            values = postings[token]
            document_frequency = len(values)
            idf.append(
                math.log(1.0 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5))
            )
            posting_rows.extend(row for row, _ in values)
            term_frequencies.extend(float(frequency) for _, frequency in values)
            offsets.append(len(posting_rows))
        return cls(
            vocabulary=vocabulary,
            offsets=np.asarray(offsets, dtype=np.int64),
            posting_rows=np.asarray(posting_rows, dtype=np.int32),
            term_frequencies=np.asarray(term_frequencies, dtype=np.float32),
            idf=np.asarray(idf, dtype=np.float32),
            document_lengths=lengths,
            average_document_length=float(lengths.mean()),
            k1=float(k1),
            b=float(b),
        )

    def score(self, query: str, allowed_mask: np.ndarray | None = None) -> np.ndarray:
        if allowed_mask is not None:
            allowed_mask = np.asarray(allowed_mask, dtype=bool)
            if allowed_mask.shape != (self.document_count,):
                raise ValueError("BM25 allowed mask has the wrong shape")
        scores = np.zeros(self.document_count, dtype=np.float32)
        vocabulary_lookup = {term: index for index, term in enumerate(self.vocabulary)}
        query_terms = Counter(tokenize_multilingual(query))
        length_norm = 1.0 - self.b + self.b * (
            self.document_lengths / max(self.average_document_length, 1e-9)
        )
        for token, query_frequency in query_terms.items():
            term_index = vocabulary_lookup.get(token)
            if term_index is None:
                continue
            start = int(self.offsets[term_index])
            end = int(self.offsets[term_index + 1])
            rows = self.posting_rows[start:end]
            frequencies = self.term_frequencies[start:end]
            denominator = frequencies + self.k1 * length_norm[rows]
            contribution = self.idf[term_index] * (
                frequencies * (self.k1 + 1.0) / denominator
            )
            scores[rows] += contribution.astype(np.float32) * float(query_frequency)
        if allowed_mask is not None:
            scores[~allowed_mask] = -np.inf
        return scores

    def save(self, index_path: Path, vocabulary_path: Path) -> None:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            index_path,
            offsets=self.offsets,
            posting_rows=self.posting_rows,
            term_frequencies=self.term_frequencies,
            idf=self.idf,
            document_lengths=self.document_lengths,
            average_document_length=np.asarray([self.average_document_length], dtype=np.float64),
            k1=np.asarray([self.k1], dtype=np.float64),
            b=np.asarray([self.b], dtype=np.float64),
        )
        vocabulary_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "tokenizer_version": "unicode_fold_v1",
                    "document_count": self.document_count,
                    "term_count": len(self.vocabulary),
                    "vocabulary": self.vocabulary,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, index_path: Path, vocabulary_path: Path) -> "BM25Index":
        metadata = json.loads(vocabulary_path.read_text(encoding="utf-8"))
        with np.load(index_path, allow_pickle=False) as values:
            index = cls(
                vocabulary=list(metadata["vocabulary"]),
                offsets=values["offsets"],
                posting_rows=values["posting_rows"],
                term_frequencies=values["term_frequencies"],
                idf=values["idf"],
                document_lengths=values["document_lengths"],
                average_document_length=float(values["average_document_length"][0]),
                k1=float(values["k1"][0]),
                b=float(values["b"][0]),
            )
        index.verify()
        if index.document_count != int(metadata["document_count"]):
            raise AssertionError("BM25 document count does not match vocabulary metadata")
        return index

    def verify(self) -> None:
        if len(self.offsets) != len(self.vocabulary) + 1:
            raise AssertionError("BM25 offsets are invalid")
        if int(self.offsets[0]) != 0 or int(self.offsets[-1]) != len(self.posting_rows):
            raise AssertionError("BM25 postings bounds are invalid")
        if len(self.posting_rows) != len(self.term_frequencies):
            raise AssertionError("BM25 posting rows and frequencies differ")
        if len(self.idf) != len(self.vocabulary):
            raise AssertionError("BM25 IDF vector is invalid")
        if np.any(self.posting_rows < 0) or np.any(self.posting_rows >= self.document_count):
            raise AssertionError("BM25 posting contains an invalid document row")
        if not np.isfinite(self.idf).all() or not np.isfinite(self.document_lengths).all():
            raise AssertionError("BM25 index contains non-finite values")
