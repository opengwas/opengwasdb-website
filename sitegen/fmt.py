"""How numbers, dates, sizes and catalogue codes are written on the site."""
from datetime import date, datetime

NBSP = " "

ANCESTRY = {
    "EUR": "European", "AFR": "African", "AMR": "Admixed American", "EAS": "East Asian",
    "SAS": "South Asian", "META": "Multi-ancestry meta-analysis", "unassigned": "Not yet assigned",
}

# Plain-English labels for coded catalogue values. Anything missing falls back
# to the code with underscores turned into spaces.
LABELS = {
    "layout": {"dense": "Dense", "ragged": "Ragged", "hybrid": "Hybrid"},
    "completion_state": {"reference_completed": "Imputed (reference-completed)", "observed_only": "Observed values only"},
    "association_coverage": {"gwas": "Genome-wide", "signals_only": "Significant signals only", "cis": "cis-QTL"},
    "sample_size_kind": {"case_control": "Cases and controls", "total": "Total", "variant_level": "Varies by variant"},
    "effect_scale": {"sd": "Standard deviation units", "log_or": "Log odds ratio"},
    "ancestry_method": {"af_assigned": "Assigned from allele frequencies", "source_fallback": "As reported by the source",
                        "unassigned": "Not yet assigned"},
    "ontology_method": {"source_provided": "Provided by the source", "unmapped": "Not mapped yet"},
    "tissue": {"whole_blood": "Whole blood", "plasma": "Plasma"},
    "trait_class": {"phenotype": "Phenotype", "molecular": "Molecular trait"},
    "outcome_type": {"binary": "Binary", "continuous": "Continuous"},
}


def label(kind: str, code) -> str:
    if code is None or code == "":
        return ""
    return LABELS.get(kind, {}).get(code) or str(code).replace("_", " ").capitalize()


def ancestry(code) -> str:
    return ANCESTRY.get(code or "unassigned", code)


def nf(n) -> str:
    """12,345"""
    return f"{int(n):,}"


def _date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def fdate(value) -> str:
    """2 November 2026"""
    d = _date(value)
    return f"{d.day} {d:%B %Y}"


def isodate(value) -> str:
    return _date(value).isoformat()


def fms(ms: float) -> str:
    """Query time: 4.2 ms, 45 ms, 2.2 s"""
    if ms < 10:
        return f"{ms:.1f}{NBSP}ms"
    if ms < 1000:
        return f"{round(ms)}{NBSP}ms"
    return f"{ms / 1000:.1f}{NBSP}s"


def fbytes(n: int) -> str:
    """Decimal units, as disks are sold: 2.6 GB, 139 GB, 4.1 TB"""
    gb = n / 1e9
    if gb >= 1000:
        return f"{gb / 1000:.1f}{NBSP}TB"
    if gb >= 10:
        return f"{round(gb):,}{NBSP}GB"
    return f"{gb:.1f}{NBSP}GB"


def fsize(n: int) -> str:
    """File size, in decimal units: 70 KB, 1.1 MB, 31 MB"""
    for unit, scale in (("GB", 1e9), ("MB", 1e6), ("KB", 1e3)):
        if n >= scale:
            v = n / scale
            return f"{v:.1f}{NBSP}{unit}" if v < 10 else f"{round(v):,}{NBSP}{unit}"
    return f"{n}{NBSP}bytes"


def join_and(items) -> str:
    items = list(items)
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]
