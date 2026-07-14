from app import screening


def test_china_phone_flags_peer():
    r = screening.screen({"domain": "gldled.com", "phone": "+8613809866355"})
    assert r["country"] == "China" and r["excluded"]
    assert "同行" in r["exclude_reason"]


def test_china_phone_with_00_prefix():
    # real data had +008675523570137 (enbon.com)
    r = screening.screen({"domain": "enbon.com", "phone": "+008675523570137"})
    assert r["country"] == "China" and r["excluded"]


def test_cn_tld_flags_peer_without_phone():
    assert screening.screen({"domain": "szled.cn"})["country"] == "China"


def test_chinese_email_domain_flags_peer():
    r = screening.screen({"domain": "some-host.com", "email": "sales@sz-led.cn"})
    assert r["country"] == "China" and r["excluded"]


def test_directory_site_excluded():
    for host in ("alibaba.com", "justdial.com", "kompass.com", "aeroleads.com", "korea.tradekey.com"):
        r = screening.screen({"domain": host})
        assert r["excluded"], host
        assert r["exclude_reason"] == "B2B 目录站/平台"


def test_real_buyer_not_excluded():
    r = screening.screen({"domain": "arasystem.kr", "phone": "+827048950794"})
    assert r["country"] == "South Korea" and not r["excluded"]


def test_custom_exclude_country():
    cand = {"domain": "ledindia.in", "phone": "+919876543210"}
    assert screening.screen(cand)["excluded"] is False  # not excluded by default
    r = screening.screen(cand, exclude_countries=["India", "Pakistan"])
    assert r["excluded"] and r["exclude_reason"] == "排除国家（India）"


def test_peer_filter_can_be_turned_off():
    r = screening.screen({"domain": "gldled.com", "phone": "+8613809866355"}, exclude_peers=False)
    assert r["country"] == "China" and not r["excluded"]


def test_unknown_country_never_excluded():
    r = screening.screen({"domain": "mystery.io"}, exclude_countries=["India"])
    assert r["country"] is None and not r["excluded"]


def test_usa_phone_not_confused_with_longer_codes():
    assert screening.detect_country({"phone": "+16162021473"}) == "USA/Canada"
    assert screening.detect_country({"phone": "+971529357710"}) == "UAE"
    assert screening.detect_country({"phone": "+8613427921400"}) == "China"
