"""Camada central de normalização e agregação analítica; nunca modifica os dados de origem."""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any, Iterable

MISSING = "NÃO INFORMADO"
STATE_REGIONS = {
    "NORTE": {"AC": "ACRE", "AP": "AMAPA", "AM": "AMAZONAS", "PA": "PARA", "RO": "RONDONIA", "RR": "RORAIMA", "TO": "TOCANTINS"},
    "NORDESTE": {"AL": "ALAGOAS", "BA": "BAHIA", "CE": "CEARA", "MA": "MARANHAO", "PB": "PARAIBA", "PE": "PERNAMBUCO", "PI": "PIAUI", "RN": "RIO GRANDE DO NORTE", "SE": "SERGIPE"},
    "CENTRO-OESTE": {"DF": "DISTRITO FEDERAL", "GO": "GOIAS", "MT": "MATO GROSSO", "MS": "MATO GROSSO DO SUL"},
    "SUDESTE": {"ES": "ESPIRITO SANTO", "MG": "MINAS GERAIS", "RJ": "RIO DE JANEIRO", "SP": "SAO PAULO"},
    "SUL": {"PR": "PARANA", "RS": "RIO GRANDE DO SUL", "SC": "SANTA CATARINA"},
}
_STATE_LOOKUP: dict[str, tuple[str, str]] = {}
for _region, _states in STATE_REGIONS.items():
    for _uf, _name in _states.items():
        _STATE_LOOKUP[_uf] = (_uf, _region)
        _STATE_LOOKUP[_name] = (_uf, _region)


def normalized_text(value: Any) -> str:
    """Lowercase, remove accents/punctuation, normalize whitespace for comparisons."""
    text = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def display_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def digits_only(value: Any) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def valid_provider_document(value: Any) -> bool:
    """Documento válido para identificação analítica: 11 ou 14 dígitos, não repetidos.

    Não recalcula dígitos verificadores, pois planilhas históricas podem conter erros
    nesses dígitos; documentos com tamanho inválido ou sequência repetida usam razão social.
    """
    digits = digits_only(value)
    return len(digits) in (11, 14) and len(set(digits)) > 1


def _get(row: Any, attr: str, *keys: str) -> Any:
    if isinstance(row, dict):
        if attr in row:
            return row.get(attr)
        data = row.get("data") or {}
    else:
        if hasattr(row, attr):
            val = getattr(row, attr)
            if val is not None:
                return val
        data = getattr(row, "data", {}) or {}
    if isinstance(data, dict):
        wanted = {normalized_text(k).replace(" ", "") for k in keys}
        for key, value in data.items():
            if normalized_text(key).replace(" ", "") in wanted:
                return value
    return ""


def provider_identity(row: Any) -> tuple[str, str]:
    """Identidade única: documento válido; caso contrário razão social; sem ambos, ID da linha."""
    document = _get(row, "tax_id", "CNPJCPF", "CNPJ/CPF", "CNPJ CPF")
    doc_digits = digits_only(document)
    if valid_provider_document(doc_digits):
        return ("document", doc_digits)
    name = _get(row, "business_name", "RAZÃO SOCIAL", "RAZAO SOCIAL")
    normalized_name = normalized_text(name)
    if normalized_name:
        return ("business_name", normalized_name)
    row_id = _get(row, "id", "ID INTERNO")
    return ("row", str(row_id if row_id not in (None, "") else id(row)))


def normalize_uf(value: Any) -> tuple[str, str]:
    """Retorna (sigla, região); não tenta deduzir município nem valor desconhecido."""
    key = normalized_text(value).replace(" ", "").upper() if len(normalized_text(value)) == 2 else normalized_text(value).upper()
    found = _STATE_LOOKUP.get(key)
    return found if found else (MISSING, MISSING)


def matches_filter(row: Any, filters: dict[str, str]) -> bool:
    fields = {
        "specialty": _get(row, "specialty", "ESPECIALIDADE"),
        "municipality": _get(row, "municipality", "MUNICÍPIO", "MUNICIPIO"),
        "uf": _get(row, "uf", "UF"),
        "region": normalize_uf(_get(row, "uf", "UF"))[1],
    }
    for key, criterion in filters.items():
        needle = normalized_text(criterion)
        if needle and needle not in normalized_text(fields.get(key, "")):
            return False
    return True


def deduplicate_providers(rows: Iterable[Any]) -> dict[tuple[str, str], list[Any]]:
    """Única rotina de agrupamento de prestadores reutilizada por todas as métricas."""
    groups: dict[tuple[str, str], list[Any]] = {}
    for row in rows:
        groups.setdefault(provider_identity(row), []).append(row)
    return groups


def _specialty_groups(groups: dict[tuple[str, str], list[Any]]) -> list[dict[str, Any]]:
    labels: dict[str, str] = {}
    members: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for identity, rows in groups.items():
        for row in rows:
            label = display_text(_get(row, "specialty", "ESPECIALIDADE"))
            key = normalized_text(label)
            if not key:
                continue
            labels.setdefault(key, label)
            members[key].add(identity)
    out = [{"key": key, "label": labels[key], "count": len(ids)} for key, ids in members.items()]
    return sorted(out, key=lambda item: (-item["count"], normalized_text(item["label"])))


def _region_groups(groups: dict[tuple[str, str], list[Any]]) -> tuple[list[dict[str, Any]], int]:
    counts: dict[str, int] = defaultdict(int)
    states: dict[str, set[str]] = defaultdict(set)
    without_uf = 0
    for rows in groups.values():
        # Prioriza a primeira UF válida disponível para aquele prestador; sem UF válida,
        # inclui o prestador em NÃO INFORMADO para que a partição feche exatamente.
        chosen = (MISSING, MISSING)
        for row in rows:
            candidate = normalize_uf(_get(row, "uf", "UF"))
            if candidate[0] != MISSING:
                chosen = candidate
                break
        uf, region = chosen
        counts[region] += 1
        if uf == MISSING:
            without_uf += 1
        else:
            states[region].add(uf)
    total = len(groups)
    order = ["NORTE", "NORDESTE", "CENTRO-OESTE", "SUDESTE", "SUL", MISSING]
    result = []
    for region in order:
        count = counts.get(region, 0)
        if count:
            result.append({"label": region, "count": count, "share": round(count * 100 / total, 2) if total else 0,
                           "states": sorted(states.get(region, set()))})
    return result, without_uf


def aggregate_providers(rows: Iterable[Any], filters: dict[str, str] | None = None) -> dict[str, Any]:
    """Calcula KPIs, distribuição regional, rankings e auditoria sobre uma só deduplicação."""
    filtered = [row for row in rows if matches_filter(row, filters or {})]
    groups = deduplicate_providers(filtered)
    total = len(groups)
    by_region, missing_uf = _region_groups(groups)
    specialties = _specialty_groups(groups)
    top = specialties[:10]
    bottom = sorted(specialties, key=lambda item: (item["count"], normalized_text(item["label"])))[:10]

    methods = defaultdict(int)
    priority_ids: set[tuple[str, str]] = set()
    municipalities: set[str] = set()
    for identity, members in groups.items():
        methods[identity[0]] += 1
        for row in members:
            priority = normalized_text(_get(row, "priority", "PRIORIDADE"))
            if priority in {"sim", "alta", "prioritario", "prioritaria"}:
                priority_ids.add(identity)
            municipality = normalized_text(_get(row, "municipality", "MUNICÍPIO", "MUNICIPIO"))
            if municipality:
                municipalities.add(municipality)

    raw_count = len(filtered)
    raw_missing_uf = sum(1 for row in filtered if normalize_uf(_get(row, "uf", "UF"))[0] == MISSING)
    return {
        "total_records": total,
        "total_providers": total,
        "raw_records": raw_count,
        "unique_by_document": methods["document"],
        "unique_by_business_name": methods["business_name"],
        "unique_without_document_or_name": methods["row"],
        "duplicates_removed": raw_count - total,
        "priority": len(priority_ids),
        "municipalities": len(municipalities),
        "specialty_count": len(specialties),
        "by_region": by_region,
        "by_specialty": top,
        "top_specialties": top,
        "smallest_specialties": bottom,
        "normalized_specialties": [{"key": item["key"], "label": item["label"], "providers": item["count"]} for item in specialties],
        "providers_without_valid_uf": missing_uf,
        "records_without_valid_uf": raw_missing_uf,
        "region_sum_matches_total": sum(item["count"] for item in by_region) == total,
        "specialty_types": {"status": "awaiting_official_mapping", "count": None, "mapping_attached": False},
        "status": "ok",
    }
