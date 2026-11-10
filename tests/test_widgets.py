import pytest

from newtgapi.exceptions import ValidationError
from newtgapi.widgets import (
    HtmlWidget,
    parse_widget_query_data,
    validate_widget_data,
    validate_widget_html,
    validate_widget_size,
)


def test_builder_escapes_user_input():
    html = HtmlWidget(title="<script>").text("<b>hi</b>").button("A&B", data='x"y').render()
    assert "<title>&lt;script&gt;</title>" in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;hi&lt;/b&gt;" in html
    assert "A&amp;B" in html


def test_builder_ton_buttons_set_query_type():
    html = HtmlWidget().ton_sign_button().ton_transaction_button().render()
    assert 'data-query-type="sign"' in html
    assert 'data-query-type="transaction"' in html


def test_validate_html_rejects_empty_and_oversize():
    with pytest.raises(ValidationError):
        validate_widget_html("")
    with pytest.raises(ValidationError):
        validate_widget_html("x" * (64 * 1024 + 1))


def test_validate_size_bounds():
    assert validate_widget_size(320, 240) == (320, 240)
    with pytest.raises(ValidationError):
        validate_widget_size(0, 10)
    with pytest.raises(ValidationError):
        validate_widget_size(10, 99999)
    with pytest.raises(ValidationError):
        validate_widget_size(True, 10)  # bool is not a valid int here


def test_validate_data_dict_and_size():
    assert validate_widget_data({"a": 1}) == '{"a":1}'
    assert validate_widget_data("plain") == "plain"
    with pytest.raises(ValidationError):
        validate_widget_data("x" * 5000)


def test_parse_widget_query_data():
    assert parse_widget_query_data('{"a": 1}') == {"a": 1}
    assert parse_widget_query_data("hello") == "hello"
    assert parse_widget_query_data(None) is None
