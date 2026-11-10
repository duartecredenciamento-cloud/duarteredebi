from app.analytics import MISSING, STATE_REGIONS, aggregate_providers, normalize_uf, provider_identity


def row(i, tax_id="", name="", specialty="", uf="", municipality="", priority="", specialty_type=""):
    data = {"TIPO ESPECIALIDADE": specialty_type} if specialty_type else {}
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
    assert types["source_column"] == "TIPO ESPECIALIDADE"


def test_state_series_uses_same_unique_provider_identity():
    result = aggregate_providers([
        row(1, "12345678901", "A", "Cardiologia", "SP"),
        row(2, "12345678901", "A", "Cardiologia", "SP"),
        row(3, "", "B", "Ortopedia", "BA"),
        row(4, "", "C", "", "Campinas"),
    ])
    by_state = {item["uf"]: item["count"] for item in result["by_state"]}
    assert by_state == {"BA": 1, "SP": 1}
    assert sum(by_state.values()) + result["providers_without_valid_uf"] == result["total_providers"]


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
    assert 'id="kSpecialties"' in html and 'id="specialtiesBottom"' in html
    assert 'id="statuses"' not in html and 'STATUS ATIVO' not in html
