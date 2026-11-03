"""Portable preparation contracts. Intervals are half-open; video times are frames."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass
class Finding:
    code: str
    severity: str
    artifact_id: str
    location: str
    message: str
    remedy_id: str

@dataclass
class SourceRef:
    source_id: str
    path: str
    heading: str = ''
    pages: list[int] = field(default_factory=list)
    sha256: str = ''
    category: str = ''

@dataclass
class SourceManifest:
    schema_version: int
    snapshot_id: str
    records: list[SourceRef]
    required_decks: list[str]

@dataclass
class TeachingBinding:
    concept_id: str
    primary_beats: list[str]
    supporting_beats: list[str]
    source_refs: list[str]
    explanation_claim: str
    mechanism: str
    example_ids: list[str]
    prediction_pairs: list[list[str]]
    review: str = 'not_reviewed'

@dataclass
class ExampleSpec:
    example_id: str
    adapter: str
    inputs: dict
    assumptions: list[str]
    expected: Any
    verifier: str
    source_refs: list[str]

@dataclass
class NarrationAsset:
    beat_id: str
    written_hash: str
    spoken_hash: str
    configuration_hash: str
    wav_hash: str
    sample_rate: int
    sample_count: int

@dataclass
class WordAlignment:
    narration_identity: str
    aligner_identity: str
    token_mapping: list
    intervals: list
    provenance: list[str]
    mismatch_spans: list = field(default_factory=list)
    corrections: list = field(default_factory=list)

@dataclass
class PhraseAnchor:
    phrase: str
    occurrence: int = 1
    frame_offset: int = 0

@dataclass
class BeatTimeline:
    beat_id: str
    frames: int
    speech: tuple[int,int]
    moves: list[dict]
    captions: list = field(default_factory=list)
    reading: tuple[int,int] | None = None
    prediction: tuple[int,int] | None = None
    cleanup: tuple[int,int] | None = None

@dataclass
class DishTimeline:
    dish_id: str
    fps: int
    beats: list[BeatTimeline]
    total_frames: int
    fingerprint: str = ''

@dataclass
class AssemblyPlan:
    output_id: str
    members: list[str]
    offsets: dict[str,int]
    total_frames: int

@dataclass
class RenderReceipt:
    input_fingerprint: str
    profile: str
    output_hashes: dict
    media_metadata: dict
    findings: list

@dataclass
class ReviewDecision:
    artifact_hash: str
    reviewer: str
    timestamp: str
    category: str
    result: str
    notes: str

@dataclass
class ResourceCatalog:
    notes: dict
    concepts: dict
    lectures: dict
    examples: dict
    formulas: dict
    exercises: dict
    corrections: dict
    figures: dict
    aliases: dict
