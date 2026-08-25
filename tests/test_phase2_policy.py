from devoteam_reference_ai.phase2_policy import classify_path, is_blocked_header, may_follow_links


CONFIG = {
    "exclusions": {
        "never_ingest_headers": ["Valeur Projet", "Équipe Intervenante"],
        "never_follow_link_headers": ["Site web", "Logo"],
        "excluded_path_terms": ["CV", "Documents personnels"],
    }
}


def test_sensitive_headers_are_blocked_accent_insensitively():
    assert is_blocked_header("Equipe Intervenante", CONFIG)
    assert is_blocked_header("Valeur projet", CONFIG)
    assert not may_follow_links("Équipe Intervenante", CONFIG)


def test_website_and_logo_links_are_not_evidence():
    assert not may_follow_links("Site Web", CONFIG)
    assert not may_follow_links("logo", CONFIG)
    assert may_follow_links("Client", CONFIG)


def test_excluded_source_path():
    assert classify_path("root/CV/consultant.pdf", CONFIG)[0]
    assert not classify_path("root/Attestations/reference.pdf", CONFIG)[0]
