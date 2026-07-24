import datetime as dt

import pytest

from app import dedupe, opportunities, repository


def _lead(conn, no=100):
    conn.execute(
        "INSERT INTO leads(no, company_en, country) VALUES (?, ?, ?)",
        (no, f"Buyer {no}", "USA"),
    )
    conn.commit()
    return no


def test_create_list_and_weighted_stats(conn):
    no = _lead(conn)
    item = opportunities.create(conn, no, {
        "title": "Church P2.5 wall",
        "amount": 20000,
        "expected_close_date": "2026-07-30",
        "next_action": "确认图纸",
        "next_action_date": "2026-07-20",
    })
    assert item["stage"] == "qualified"
    assert item["probability"] == 20
    assert item["weighted_amount"] == 4000
    rows = opportunities.list_all(conn, lead_no=no, today=dt.date(2026, 7, 24))
    assert rows[0]["overdue"] is True
    stats = opportunities.stats(conn, today=dt.date(2026, 7, 24))
    assert stats["open_count"] == 1
    assert stats["open_amount"] == 20000
    assert stats["weighted_amount"] == 4000
    assert stats["closing_this_month"] == 20000
    assert stats["attention_count"] == 1
    assert stats["overdue_count"] == 1


def test_stage_requirements_prevent_fake_progress(conn):
    no = _lead(conn)
    item = opportunities.create(conn, no, {"title": "Outdoor billboard"})
    with pytest.raises(opportunities.OpportunityValidation, match="报价金额"):
        opportunities.update(conn, item["id"], {"stage": "quoted"})
    quoted = opportunities.update(conn, item["id"], {
        "stage": "quoted",
        "amount": 45000,
        "next_action": "周五确认付款条款",
    })
    assert quoted["probability"] == 60
    assert conn.execute("SELECT stage FROM leads WHERE no=?", (no,)).fetchone()["stage"] == "negotiating"
    with pytest.raises(opportunities.OpportunityValidation, match="丢单原因"):
        opportunities.update(conn, item["id"], {"stage": "lost"})


def test_won_requires_amount_and_updates_lead(conn):
    no = _lead(conn)
    item = opportunities.create(conn, no, {"title": "Rental batch"})
    with pytest.raises(opportunities.OpportunityValidation, match="成交金额"):
        opportunities.update(conn, item["id"], {"stage": "won"})
    won = opportunities.update(conn, item["id"], {"stage": "won", "amount": 86000})
    assert won["probability"] == 100
    assert won["weighted_amount"] == 86000
    assert conn.execute("SELECT stage FROM leads WHERE no=?", (no,)).fetchone()["stage"] == "won"


def test_stale_threshold_and_attention_sort(conn):
    no = _lead(conn)
    stale = opportunities.create(conn, no, {"title": "Stale project"})
    fresh = opportunities.create(conn, no, {
        "title": "Fresh project", "next_action_date": "2026-07-23"})
    conn.execute(
        "UPDATE opportunities SET last_activity_at='2026-07-01T00:00:00+00:00'"
        " WHERE id=?",
        (stale["id"],),
    )
    conn.commit()
    attention = opportunities.list_all(
        conn, attention=True, today=dt.date(2026, 7, 24))
    assert [r["id"] for r in attention] == [fresh["id"], stale["id"]]
    assert attention[0]["overdue"] is True
    assert attention[1]["stale"] is True


def test_attention_count_does_not_double_count_overdue_stale_project(conn):
    no = _lead(conn)
    item = opportunities.create(conn, no, {
        "title": "Overdue and stale",
        "next_action_date": "2026-07-20",
    })
    conn.execute(
        "UPDATE opportunities SET last_activity_at='2026-07-01T00:00:00+00:00'"
        " WHERE id=?",
        (item["id"],),
    )
    conn.commit()
    summary = opportunities.stats(conn, today=dt.date(2026, 7, 24))
    assert summary["overdue_count"] == 1
    assert summary["stale_count"] == 1
    assert summary["attention_count"] == 1


def test_note_and_reply_refresh_open_deal_activity(conn):
    no = _lead(conn)
    item = opportunities.create(conn, no, {"title": "Active project"})
    old = "2026-01-01T00:00:00+00:00"
    conn.execute(
        "UPDATE opportunities SET last_activity_at=?, updated_at=? WHERE id=?",
        (old, old, item["id"]),
    )
    conn.commit()
    repository.add_note(conn, no, "客户确认需要 P1.86")
    after_note = opportunities.get(conn, item["id"])
    assert after_note["last_activity_at"] != old

    conn.execute(
        "UPDATE opportunities SET last_activity_at=?, updated_at=? WHERE id=?",
        (old, old, item["id"]),
    )
    conn.commit()
    repository.mark_replied(conn, no, "email")
    assert opportunities.get(conn, item["id"])["last_activity_at"] != old


def test_validation_bounds(conn):
    no = _lead(conn)
    with pytest.raises(opportunities.OpportunityValidation, match="项目名称"):
        opportunities.create(conn, no, {"title": " "})
    with pytest.raises(opportunities.OpportunityValidation, match="0-100"):
        opportunities.create(conn, no, {"title": "X", "probability": 120})
    with pytest.raises(opportunities.OpportunityValidation, match="YYYY-MM-DD"):
        opportunities.create(conn, no, {"title": "X", "expected_close_date": "tomorrow"})


def test_dedupe_repoints_opportunities_without_data_loss(conn):
    keep = _lead(conn, 100)
    dup = _lead(conn, 101)
    conn.execute("UPDATE leads SET website='buyer.com' WHERE no IN (?,?)", (keep, dup))
    conn.commit()
    item = opportunities.create(conn, dup, {"title": "Real P3.91 project", "amount": 12000})
    dedupe.merge_leads(conn, keep, [dup])
    moved = opportunities.get(conn, item["id"])
    assert moved["lead_no"] == keep
    assert moved["amount"] == 12000
