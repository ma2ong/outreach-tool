import pytest

from app import icp
from app.db import connect, init_schema


def test_classify_rental_highest():
    r = icp.classify_text("We offer LED screen RENTAL for concerts and festival staging.")
    assert r["icp_type"] == "rental"
    assert r["fit_score"] >= 90


def test_classify_integrator():
    r = icp.classify_text("Leading AV integration services and audio visual solutions.")
    assert r["icp_type"] == "integrator"


def test_classify_spanish_reseller():
    r = icp.classify_text("Somos distribuidor mayorista de pantallas LED.")
    assert r["icp_type"] == "reseller"


def test_classify_picks_higher_scoring_category():
    # both rental and signage keywords -> rental (higher base) wins
    r = icp.classify_text("Sign company also offering stage rental for events, concert equipment.")
    assert r["icp_type"] == "rental"


def test_classify_bonus_capped_at_100():
    text = " ".join(k for _, (_, ks) in icp._CATEGORIES.items() for k in ks)
    assert icp.classify_text(text)["fit_score"] <= 100


def test_classify_unknown():
    r = icp.classify_text("We bake artisanal sourdough bread.")
    assert r == {"icp_type": "unknown", "fit_score": 0, "hits": []}


@pytest.fixture
def conn(tmp_path):
    c = connect(str(tmp_path / "t.db"))
    init_schema(c)
    c.execute("INSERT INTO leads(no, company_en, website, tags) VALUES (1,'A','a.com','vip,icp:signage')")
    c.commit()
    return c


def test_apply_to_lead_sets_fit_and_replaces_icp_tag(conn):
    icp.apply_to_lead(conn, 1, {"icp_type": "rental", "fit_score": 92})
    row = conn.execute("SELECT target_fit, tags FROM leads WHERE no=1").fetchone()
    assert row["target_fit"] == "租赁公司 (92)"
    assert row["tags"] == "vip,icp:rental"  # old icp tag replaced, others kept


def test_apply_unknown_is_noop(conn):
    icp.apply_to_lead(conn, 1, {"icp_type": "unknown", "fit_score": 0})
    row = conn.execute("SELECT target_fit FROM leads WHERE no=1").fetchone()
    assert row["target_fit"] is None
