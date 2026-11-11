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
STATE_DISPLAY_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
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
        if not needle:
            continue
        if key == "uf":
            row_uf = normalize_uf(_get(row, "uf", "UF"))[0]
            criterion_uf = normalize_uf(criterion)[0]
            if criterion_uf != MISSING:
                if row_uf != criterion_uf:
                    return False
                continue
        if needle not in normalized_text(fields.get(key, "")):
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


def _state_groups(groups: dict[tuple[str, str], list[Any]]) -> list[dict[str, Any]]:
    """Conta cada prestador uma vez em cada UF válida em que está cadastrado."""
    identities_by_uf: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for identity, members in groups.items():
        for row in members:
            uf, _ = normalize_uf(_get(row, "uf", "UF"))
            if uf != MISSING:
                identities_by_uf[uf].add(identity)
    total = len(groups)
    result = [{"uf": uf, "label": STATE_DISPLAY_NAMES[uf], "count": len(identities),
               "share": round(len(identities) * 100 / total, 2) if total else 0}
              for uf, identities in identities_by_uf.items()]
    return sorted(result, key=lambda item: (-item["count"], item["label"].casefold()))


def _specialty_type_groups(rows: list[Any]) -> dict[str, Any]:
    """Usa diretamente TIPO ESPECIALIDADE por registro, sem inferir categorias."""
    grouped: dict[str, dict[str, Any]] = {}
    missing = 0
    for row in rows:
        label = display_text(_get(row, "specialty_type", "TIPO ESPECIALIDADE"))
        key = normalized_text(label)
        if key in {"", "nao informado"}:
            missing += 1
            continue
        item = grouped.setdefault(key, {"label": label, "records": 0})
        item["records"] += 1
    values = sorted(grouped.values(), key=lambda item: (-item["records"], normalized_text(item["label"])))
    return {"status": "available", "count": len(values), "values": values,
            "valid_records": sum(item["records"] for item in values), "missing_records": missing,
            "source_column": "TIPO ESPECIALIDADE",
            "note": "Classificação oficial por registro. Vazios e NÃO INFORMADO ficam fora da contagem de categorias."}


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
    by_state = _state_groups(groups)
    specialty_types = _specialty_type_groups(filtered)
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
    identified_ufs = {normalize_uf(_get(row, "uf", "UF"))[0] for row in filtered}
    identified_ufs.discard(MISSING)
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
        "by_state": by_state,
        "uf_coverage": len(identified_ufs),
        "uf_coverage_total": 27,
        "by_specialty": top,
        "top_specialties": top,
        "smallest_specialties": bottom,
        "normalized_specialties": [{"key": item["key"], "label": item["label"], "providers": item["count"]} for item in specialties],
        "providers_without_valid_uf": missing_uf,
        "records_without_valid_uf": raw_missing_uf,
        "region_sum_matches_total": sum(item["count"] for item in by_region) == total,
        "specialty_types": specialty_types,
        "status": "ok",
    }
