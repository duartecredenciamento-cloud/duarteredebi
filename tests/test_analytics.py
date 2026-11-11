from app.analytics import MISSING, STATE_REGIONS, aggregate_providers, normalize_uf, provider_identity


def row(i, tax_id="", name="", specialty="", uf="", municipality="", priority="", specialty_type=""):
    data = {"TIPO": specialty_type} if specialty_type else {}
    return {"id": i, "tax_id": tax_id, "business_name": name, "specialty": specialty,
            "uf": uf, "municipality": municipality, "priority": priority, "data": data}


def test_master_example_counts_three_unique_providers():
    rows = [
        row(1, "12.345.678/0001-90", "Empresa A"),
        row(2, "12345678000190", "Empresa A"),
        row(3, "", "Empresa B"),
        row(4, "", "Empresa B"),
        row(5, "", "Empresa C"),
    ]
    result = aggregate_providers(rows)
    assert result["total_providers"] == 3
    assert result["unique_by_document"] == 1
    assert result["unique_by_business_name"] == 2
    assert result["duplicates_removed"] == 2


def test_document_with_and_without_mask_is_same_identity():
    assert provider_identity(row(1, "12.345.678/0001-90", "A")) == provider_identity(row(2, "12345678000190", "B"))


def test_invalid_or_empty_document_falls_back_to_name_without_mixing():
    # Documento com comprimento inválido; mesma razão social de cadastro sem documento.
    assert provider_identity(row(1, "1234", "Empresa A")) == provider_identity(row(2, "", "EMPRESA   Á"))
    # Documento válido continua sendo chave documental, ainda que a razão social coincida.
    assert provider_identity(row(3, "12345678000190", "EMPRESA A")) != provider_identity(row(2, "", "EMPRESA A"))


def test_repeated_documents_and_names_are_deduplicated():
    result = aggregate_providers([row(1, "12345678901", "Nome"), row(2, "12345678901", "Outro"), row(3, "", " Loja  Dois "), row(4, "", "loja dois")])
    assert result["total_providers"] == 2
    assert result["duplicates_removed"] == 2


def test_all_federative_units_map_to_the_official_regions():
    expected = {uf: region for region, states in STATE_REGIONS.items() for uf in states}
    assert len(expected) == 27
    for uf, region in expected.items():
        assert normalize_uf(uf) == (uf, region)
        assert normalize_uf(STATE_REGIONS[region][uf]) == (uf, region)


def test_missing_or_municipality_in_uf_is_not_guessed():
    assert normalize_uf("") == (MISSING, MISSING)
    assert normalize_uf("Campinas") == (MISSING, MISSING)
    result = aggregate_providers([row(1, "", "Empresa", uf="", municipality="Campinas")])
    assert result["providers_without_valid_uf"] == 1
    assert result["by_region"] == [{"label": MISSING, "count": 1, "share": 100.0, "states": []}]


def test_top_and_bottom_specialty_rankings_exclude_zeroes_and_handle_small_sets():
    rows = []
    for i, (name, count) in enumerate([("Alpha", 5), ("Beta", 3), ("Gamma", 1)], start=1):
        for j in range(count):
            rows.append(row(i * 100 + j, f"{i * 100 + j:011d}", f"provider {i}-{j}", name))
    result = aggregate_providers(rows)
    assert [(x["label"], x["count"]) for x in result["top_specialties"]] == [("Alpha", 5), ("Beta", 3), ("Gamma", 1)]
    assert [(x["label"], x["count"]) for x in result["smallest_specialties"]] == [("Gamma", 1), ("Beta", 3), ("Alpha", 5)]
    assert len(result["top_specialties"]) == 3
    assert all(x["count"] > 0 for x in result["smallest_specialties"])


def test_specialty_type_reads_official_column_and_excludes_missing_values():
    result = aggregate_providers([
        row(1, "12345678901", "A", "Cardiologia", specialty_type="CLÍNICA MÉDICA"),
        row(2, "12345678902", "B", "Odontologia", specialty_type="CLÍNICA MÉDICA"),
        row(3, "12345678903", "C", "Cardiologia", specialty_type="NÃO INFORMADO"),
        row(4, "12345678904", "D", "Odontologia", specialty_type=""),
    ])
    types = result["specialty_types"]
    assert types["count"] == 1
    assert types["values"] == [{"label": "CLÍNICA MÉDICA", "records": 2}]
    assert types["valid_records"] == 2 and types["missing_records"] == 2
    assert types["source_column"] == "TIPO"



def test_specialty_type_never_falls_back_to_specialty_or_legacy_fields():
    rows = [
        {"id": 1, "business_name": "A", "specialty": "Centro de Diagnóstico",
         "specialty_type": "Centro de Diagnóstico", "data": {"ESPECIALIDADE": "Centro de Diagnóstico", "TIPO ESPECIALIDADE": "Centro de Diagnóstico"}},
        {"id": 2, "business_name": "B", "ESPECIALIDADE": "Hospital",
         "TIPO": "HOSPITAL"},
    ]
    types = aggregate_providers(rows)["specialty_types"]
    assert types["values"] == [{"label": "HOSPITAL", "records": 1}]
    assert types["count"] == 1
    assert types["valid_records"] == 1 and types["missing_records"] == 1
    assert types["source_column"] == "TIPO"


def test_state_series_uses_unique_provider_identity_and_keeps_unknown_separate():
    result = aggregate_providers([
        row(1, "12345678901", "A", "Cardiologia", "SP"),
        row(2, "12345678901", "A", "Cardiologia", "SP"),
        row(3, "", "B", "Ortopedia", "BA"),
        row(4, "", "C", "", "Campinas"),
    ])
    by_state = {item["uf"]: item for item in result["by_state"]}
    assert {uf: item["count"] for uf, item in by_state.items()} == {"BA": 1, "SP": 1}
    assert by_state["SP"]["label"] == "São Paulo"
    assert result["providers_without_valid_uf"] == 1
    assert result["uf_coverage"] == 2 and result["uf_coverage_total"] == 27


def test_provider_registered_in_multiple_ufs_counts_once_in_each_state():
    result = aggregate_providers([
        row(1, "12345678901", "A", "Cardiologia", "SP"),
        row(2, "12345678901", "A", "Cardiologia", "RJ"),
        row(3, "", "B", "Ortopedia", "Campinas"),
    ])
    assert result["total_providers"] == 2
    assert [(x["uf"], x["count"]) for x in result["by_state"]] == [("RJ", 1), ("SP", 1)]
    assert result["providers_without_valid_uf"] == 1
    assert result["uf_coverage"] == 2


def test_dashboard_totals_region_and_specialty_groups_reconcile():
    rows = [row(1, "12345678901", "A", "Cardiologia", "SP"), row(2, "12345678901", "A", "Cardiologia", "SP"),
            row(3, "", "B", "Ortopedia", "BA"), row(4, "", "C", "", "Campinas")]
    result = aggregate_providers(rows)
    assert result["total_providers"] == 3
    assert sum(x["count"] for x in result["by_region"]) == result["total_providers"]
    assert result["region_sum_matches_total"] is True
    assert sum(x["count"] for x in result["top_specialties"]) >= 2


def test_filters_are_applied_before_shared_deduplication():
    rows = [row(1, "12345678901", "A", "Cardiologia", "SP"), row(2, "12345678901", "A", "Ortopedia", "SP"),
            row(3, "", "B", "Ortopedia", "BA")]
    filtered = aggregate_providers(rows, {"specialty": "cardiologia"})
    assert filtered["total_providers"] == 1
    assert [x["label"] for x in filtered["top_specialties"]] == ["Cardiologia"]
    assert filtered["region_sum_matches_total"] is True
    assert filtered["uf_coverage"] == 1
    assert [(x["uf"], x["count"]) for x in filtered["by_state"]] == [("SP", 1)]


def test_all_specialties_are_available_beyond_top_ten_and_sorted_by_unique_providers():
    rows = []
    for i in range(15):
        specialty = f"Especialidade {i + 1:02d}"
        for j in range(15 - i):
            rows.append(row(1000 + i * 20 + j, f"{i * 100 + j + 1:011d}", f"Prestador {i}-{j}", specialty))
    # A duplicated row for the first provider must not increase its specialty count.
    rows.append(row(9999, "00000000001", "Prestador 0-0", "Especialidade 01"))
    result = aggregate_providers(rows)
    all_specialties = result["normalized_specialties"]
    assert len(all_specialties) == 15
    assert len(result["top_specialties"]) == 10
    assert all_specialties[0]["label"] == "Especialidade 01"
    assert all_specialties[0]["providers"] == 15
    assert all_specialties[-1]["label"] == "Especialidade 15"
    assert [item["providers"] for item in all_specialties] == sorted((item["providers"] for item in all_specialties), reverse=True)


def test_frontend_has_responsive_breakpoints_and_login_hidden_rule():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    css = (root / "app/static/app.css").read_text(encoding="utf-8")
    html = (root / "app/static/index.html").read_text(encoding="utf-8")
    assert "@media(max-width:760px)" in css and "@media(max-width:390px)" in css
    assert "[hidden]{display:none!important}" in css
    assert 'id="login"' in html and 'id="app" hidden' in html
    assert 'EXECUTIVE INTELLIGENCE' in html and '/static/logo.png' in html
    assert 'id="brazilMap"' in html and 'id="refreshDashboard"' in html
    assert 'id="kSpecialties"' in html and 'id="kStates"' in html
    assert 'id="stateProviders"' in html and 'specialtiesBottom' not in html
    assert 'COBERTURA DE UF' in html and 'STATUS ATIVO' not in html
    assert '.topbar-right{flex:0 1 auto;min-width:0;justify-content:flex-end;}' in css
    assert 'state-distribution-panel' in css
    js = (root / "app/static/app.js").read_text(encoding="utf-8")
    assert "types?.source_column==='TIPO'" in js
    assert "officialTypeValues(types)" in js
    assert "normalized_specialties" in js and "renderAllSpecialties" in js
    assert "specialty-virtual-spacer" in js and "top_specialties||[]" not in js
    assert "TIPO ESPECIALIDADE" not in js
