"""
schema.py — 数据契约定义与验证

定义所有 step 脚本共用的数据模型。每个 step 的输入输出都应满足这些契约。

使用 dataclass + 简单 validation，零外部依赖。
schema 强约束让 AI 和脚本都不容易出格式错误。
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# ── 单篇论文 ──────────────────────────────────────────────────────────

@dataclass
class Paper:
    """单篇论文。schema1 中的最小论文对象。"""

    title: str
    year: Optional[int] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    citation_count: Optional[int] = None
    source: str = ""  # google_scholar | openalex | arxiv
    abstract: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None or k == "title"}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Paper":
        """从 dict 构造。容忍缺失字段，不抛异常。"""
        if not data.get("title"):
            raise ValueError("Paper missing required field: title")
        return cls(
            title=data.get("title", ""),
            year=data.get("year") if isinstance(data.get("year"), int) else None,
            authors=data.get("authors"),
            journal=data.get("journal"),
            doi=data.get("doi"),
            arxiv_id=data.get("arxiv_id"),
            citation_count=data.get("citation_count") if isinstance(data.get("citation_count"), int) else None,
            source=data.get("source", ""),
            abstract=data.get("abstract"),
        )


# ── 教授信息 ──────────────────────────────────────────────────────────

@dataclass
class Professor:
    """教授信息。"""

    name: Optional[str] = None
    affiliation: Optional[str] = None
    email_domain: Optional[str] = None
    gs_id: Optional[str] = None
    oa_id: Optional[str] = None
    orcid: Optional[str] = None
    h_index: Optional[int] = None
    i10_index: Optional[int] = None
    total_citations: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Professor":
        return cls(
            name=data.get("name"),
            affiliation=data.get("affiliation"),
            email_domain=data.get("email_domain"),
            gs_id=data.get("gs_id"),
            oa_id=data.get("oa_id"),
            orcid=data.get("orcid"),
            h_index=data.get("h_index") if isinstance(data.get("h_index"), int) else None,
            i10_index=data.get("i10_index") if isinstance(data.get("i10_index"), int) else None,
            total_citations=data.get("total_citations") if isinstance(data.get("total_citations"), int) else None,
        )


# ── SOURCE_OUTPUT（每个 step 的产出） ──────────────────────────────────

@dataclass
class SourceOutput:
    """每个数据源 step 的产出格式。详见 pipeline.md §2.2。"""

    source: str
    status: str = "success"
    error: Optional[str] = None
    professor: Optional[Professor] = None
    papers: List[Paper] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    pipeline: str = "phase1"

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "pipeline": self.pipeline,
            "source": self.source,
            "status": self.status,
            "error": self.error,
            "professor": self.professor.to_dict() if self.professor else None,
            "papers": [p.to_dict() for p in self.papers],
            "metadata": self.metadata,
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceOutput":
        if not data.get("source"):
            raise ValueError("SourceOutput missing required field: source")
        prof_data = data.get("professor")
        prof = Professor.from_dict(prof_data) if isinstance(prof_data, dict) else None
        papers_data = data.get("papers", [])
        papers = []
        for p in papers_data:
            if isinstance(p, dict) and p.get("title"):
                try:
                    papers.append(Paper.from_dict(p))
                except (ValueError, TypeError):
                    continue
        return cls(
            source=data.get("source", ""),
            status=data.get("status", "success"),
            error=data.get("error"),
            professor=prof,
            papers=papers,
            metadata=data.get("metadata"),
            pipeline=data.get("pipeline", "phase1"),
        )


# ── MERGED_OUTPUT（step6 的产出） ──────────────────────────────────────

@dataclass
class MergedPaper(Paper):
    """合并后的论文。多出 sources/source_count 字段。"""

    sources: List[str] = field(default_factory=list)
    source_count: int = 0

    @classmethod
    def from_paper(cls, paper: Paper, sources: List[str]) -> "MergedPaper":
        return cls(
            title=paper.title,
            year=paper.year,
            authors=paper.authors,
            journal=paper.journal,
            doi=paper.doi,
            arxiv_id=paper.arxiv_id,
            citation_count=paper.citation_count,
            source=paper.source,
            abstract=paper.abstract,
            sources=sources,
            source_count=len(sources),
        )

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["sources"] = self.sources
        d["source_count"] = self.source_count
        return d


@dataclass
class MergedOutput:
    """step6_merge.py 的产出。"""

    sources_used: List[str] = field(default_factory=list)
    source_status: Dict[str, str] = field(default_factory=dict)
    professor: Optional[Professor] = None
    papers: List[MergedPaper] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    pipeline: str = "phase1"
    step: str = "merge"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline": self.pipeline,
            "step": self.step,
            "sources_used": self.sources_used,
            "source_status": self.source_status,
            "professor": self.professor.to_dict() if self.professor else None,
            "papers": [p.to_dict() for p in self.papers],
            "statistics": self.statistics,
        }


# ── 验证工具 ──────────────────────────────────────────────────────────

def validate_source_output(data: Dict[str, Any], raise_on_error: bool = False) -> List[str]:
    """验证 SOURCE_OUTPUT 数据。返回问题列表（空列表表示有效）。

    Args:
        data: 原始 dict
        raise_on_error: 如果 True，发现问题直接抛 ValueError
    """
    errors = []

    if not isinstance(data, dict):
        errors.append(f"Top-level should be dict, got {type(data).__name__}")
    else:
        if "source" not in data:
            errors.append("Missing 'source' field")
        if data.get("source") not in {"google_scholar", "openalex", "arxiv"}:
            errors.append(f"Invalid source: {data.get('source')}")
        if data.get("status") not in {"success", "blocked", "empty", "error"}:
            errors.append(f"Invalid status: {data.get('status')}")
        if not isinstance(data.get("papers", []), list):
            errors.append("'papers' should be a list")
        for i, p in enumerate(data.get("papers", [])[:5]):
            if not isinstance(p, dict):
                errors.append(f"papers[{i}] should be dict")
            elif not p.get("title"):
                errors.append(f"papers[{i}] missing title")

    if raise_on_error and errors:
        raise ValueError(f"SOURCE_OUTPUT validation failed: {'; '.join(errors)}")
    return errors


def validate_merged_output(data: Dict[str, Any], raise_on_error: bool = False) -> List[str]:
    """验证 MERGED_OUTPUT 数据。"""
    errors = []

    if not isinstance(data, dict):
        errors.append(f"Top-level should be dict")
    else:
        if data.get("step") != "merge":
            errors.append(f"step field should be 'merge', got {data.get('step')}")
        if not isinstance(data.get("sources_used", []), list):
            errors.append("sources_used should be list")
        if not isinstance(data.get("papers", []), list):
            errors.append("papers should be list")

    if raise_on_error and errors:
        raise ValueError(f"MERGED_OUTPUT validation failed: {'; '.join(errors)}")
    return errors