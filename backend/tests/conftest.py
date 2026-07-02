import pytest
from app.db import connect, init_schema


@pytest.fixture
def conn(tmp_path):
    c = connect(str(tmp_path / "t.db"))
    init_schema(c)
    c.executescript("""
        INSERT INTO leads(no, company_en, country, website, instagram) VALUES
            (1, 'Alpha AV', 'USA', 'alpha.com', 'alphaig'),
            (2, 'Beta Screens', 'USA', 'beta.com', NULL),
            (3, 'Gamma LED', 'Brazil', 'gamma.com', 'gammaig');
        INSERT INTO outreach(lead_no, channel, status, touch_count, message_sent_date) VALUES
            (1, 'email', 'messaged', 1, '2026-07-01'),
            (2, 'email', 'prospect', 0, NULL),
            (1, 'instagram', 'messaged', 1, '2026-07-01'),
            (3, 'whatsapp', 'messaged', 1, '2026-06-30');
    """)
    c.commit()
    return c
