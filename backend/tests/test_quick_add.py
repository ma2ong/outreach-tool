import pytest

from app.quick_add import BadUrl, display_name, parse_url


def test_instagram_profile():
    assert parse_url("https://www.instagram.com/mccannsystems") == {"instagram": "mccannsystems"}
    assert parse_url("instagram.com/mccannsystems/") == {"instagram": "mccannsystems"}


def test_instagram_post_rejected():
    with pytest.raises(BadUrl):
        parse_url("https://www.instagram.com/p/Cxyz123/")


def test_facebook_page():
    assert parse_url("https://facebook.com/ledmarketusa") == {"facebook": "ledmarketusa"}
    assert parse_url("https://web.facebook.com/pg/somepage/about") == {"facebook": "somepage"}


def test_linkedin_company():
    assert parse_url("https://www.linkedin.com/company/mccann-systems/about/") == \
        {"linkedin": "linkedin.com/company/mccann-systems"}


def test_plain_website():
    assert parse_url("https://www.mccannsystems.com/contact-us") == {"website": "mccannsystems.com"}
    assert parse_url("mccannsystems.com") == {"website": "mccannsystems.com"}


def test_garbage_rejected():
    for bad in ("", "   ", "not a url"):
        with pytest.raises(BadUrl):
            parse_url(bad)


def test_display_name():
    assert display_name({"instagram": "mccann.systems"}) == "Mccann Systems"
    assert display_name({"website": "great-lakes-av.com"}) == "Great Lakes Av"
    assert display_name({"linkedin": "linkedin.com/company/mccann-systems"}) == "Mccann Systems"
