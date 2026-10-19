"""Rules file: matching, precedence, validation (exit 4)."""

import json

import pytest

from conftest import RULES_HEADER, TX_HEADER, assert_error, assert_ok


def _category_of(run, write, rules_text, description):
    rules = write("rules.csv", RULES_HEADER + rules_text)
    tx = write("tx.csv", TX_HEADER + f"2026-01-01,{description},-1\n")
    res = run("categorize", "--rules", rules, "--format", "json", tx)
    assert_ok(res)
    return json.loads(res.out)["transactions"][0]["category"]


def test_o6_tie_goes_to_earliest_rule(run, write):
    """O6, R4: equal priority -> rule earliest in file wins (A first)."""
    assert _category_of(run, write, "A,contains,shop,5\nB,regex,sho+p,5\n", "Shop Ltd") == "A"


def test_o6_tie_swapped_order(run, write):
    """O6, R4: equal priority with file order swapped -> B."""
    assert _category_of(run, write, "B,regex,sho+p,5\nA,contains,shop,5\n", "Shop Ltd") == "B"


@pytest.mark.parametrize("rules_text", ["A,contains,shop,5\nB,regex,sho+p,6\n", "B,regex,sho+p,6\nA,contains,shop,5\n"])
def test_o6_higher_priority_wins_regardless_of_order(run, write, rules_text):
    """O6, R4: B at priority 6 beats A at 5 in either file order."""
    assert _category_of(run, write, rules_text, "Shop Ltd") == "B"


def test_negative_priorities_compare_numerically(run, write):
    """Rules CSV (priority ^-?\\d+$), R4: -1 beats -5; 10 beats 9 (numeric, not lexical)."""
    assert _category_of(run, write, "Low,contains,x,-5\nHigh,contains,x,-1\n", "x") == "High"
    assert _category_of(run, write, "Nine,contains,x,9\nTen,contains,x,10\n", "x") == "Ten"


def test_contains_uses_casefold(run, write):
    """Rules CSV (contains = casefold substring): 'straße' matches 'STRASSE'."""
    assert _category_of(run, write, "Street,contains,straße,0\n", "Big STRASSE 5") == "Street"


def test_regex_is_search_ignorecase(run, write):
    """Rules CSV (regex = re.search IGNORECASE): unanchored search, case-insensitive."""
    assert _category_of(run, write, "Fuel,regex,sh[e]ll\\b,0\n", "the SHELL station") == "Fuel"


def test_no_match_is_uncategorized(run, write):
    """R4: no matching rule gives Uncategorized."""
    assert _category_of(run, write, "Fuel,contains,shell,0\n", "bakery") == "Uncategorized"


def test_rule_fields_are_stripped(run, write):
    """Rules CSV (stripped values): padded category/type/pattern/priority are accepted."""
    assert _category_of(run, write, "  Pad  , contains , bake , 3 \n", "bakery") == "Pad"


def test_rules_header_only_is_valid(run, write):
    """Rules CSV (zero rules valid): header-only rules file -> Uncategorized, exit 0."""
    assert _category_of(run, write, "", "anything") == "Uncategorized"


def test_rules_header_case_order_and_extra_columns(run, write):
    """Rules CSV (same header rules): stripped/lowercased names, any order, extras ignored."""
    rules = write("rules.csv", " Priority ,NOTE,Pattern,TYPE,Category\n1,ignored,cafe,contains,Dining\n")
    tx = write("tx.csv", TX_HEADER + "2026-01-01,Cafe Nero,-3\n")
    res = run("categorize", "--rules", rules, "--format", "json", tx)
    assert_ok(res)
    assert json.loads(res.out)["transactions"][0]["category"] == "Dining"


@pytest.mark.parametrize(
    "row, message",
    [
        ("Coffee,regex,(,1", "invalid regex '('"),
        ("X,glob,a,1", "invalid type 'glob'"),
        ("X,Contains,a,1", "invalid type 'Contains'"),
        ("X,contains,a,1.5", "invalid priority '1.5'"),
        ("X,contains,a,+1", "invalid priority '+1'"),
        ("  ,contains,a,1", "empty category"),
        ("X,contains,  ,1", "empty pattern"),
        ("X,contains,a", "expected 4 fields, got 3"),
        ("X,contains,a,1,extra", "expected 4 fields, got 5"),
    ],
)
def test_o8_rule_row_errors(run, write, row, message):
    """AC8, O8, R3, Error handling: invalid rule rows exit 4 with exact message and line."""
    rules = write("rules.csv", RULES_HEADER + "Ok,contains,ok,0\n" + row + "\n")
    tx = write("tx.csv", TX_HEADER)
    assert_error(run("report", "--rules", rules, tx), 4, f"{rules}:3: {message}")


@pytest.mark.parametrize(
    "row, message",
    [
        (",glob,,x", "empty category"),
        ("X,glob,,x", "invalid type 'glob'"),
        ("X,regex,,x", "empty pattern"),
        ("X,regex,(,x", "invalid priority 'x'"),
    ],
)
def test_rule_check_order(run, write, row, message):
    """Error handling (rules check order): category, type, pattern, priority, regex."""
    rules = write("rules.csv", RULES_HEADER + row + "\n")
    tx = write("tx.csv", TX_HEADER)
    assert_error(run("report", "--rules", rules, tx), 4, f"{rules}:2: {message}")


def test_rules_missing_column(run, write):
    """Error handling (missing column, first in listed order), R3: exit 4."""
    rules = write("rules.csv", "pattern,type\nx,contains\n")
    tx = write("tx.csv", TX_HEADER)
    assert_error(run("report", "--rules", rules, tx), 4, f"{rules}: missing column 'category'")


def test_rules_missing_file(run, write, tmp_path):
    """Error handling (cannot read file), R3: missing rules file exits 4."""
    tx = write("tx.csv", TX_HEADER)
    missing = tmp_path / "nope.csv"
    assert_error(run("report", "--rules", missing, tx), 4, f"{missing}: cannot read file")


def test_rules_not_utf8(run, write):
    """Error handling (not valid UTF-8), R3: exit 4."""
    rules = write("rules.csv", RULES_HEADER.encode() + b"Caf\xe9,contains,x,1\n")
    tx = write("tx.csv", TX_HEADER)
    assert_error(run("report", "--rules", rules, tx), 4, f"{rules}: not valid UTF-8")


def test_rules_missing_header(run, write):
    """Error handling (no header line: 0-byte file), R3: exit 4."""
    rules = write("rules.csv", b"")
    tx = write("tx.csv", TX_HEADER)
    assert_error(run("report", "--rules", rules, tx), 4, f"{rules}: missing header")


def test_rules_error_wins_over_transaction_error(run, write):
    """Interface (load order: rules first; first error wins): exit 4, not 3."""
    rules = write("rules.csv", RULES_HEADER + "X,glob,a,1\n")
    tx = write("tx.csv", TX_HEADER + "2026-02-30,X,-1\n")
    assert_error(run("categorize", "--rules", rules, tx), 4, f"{rules}:2: invalid type 'glob'")


@pytest.mark.parametrize(
    "header, message",
    [
        ("category,type,Pattern,pattern,priority", "duplicate column 'pattern'"),
        ("type,TYPE", "duplicate column 'type'"),
        ("type,pattern", "missing column 'category'"),
    ],
)
def test_rules_header_check_order(run, write, header, message):
    """Error handling (rules header check order: duplicate before missing), R3: exit 4."""
    rules = write("rules.csv", header + "\n")
    tx = write("tx.csv", TX_HEADER)
    assert_error(run("report", "--rules", rules, tx), 4, f"{rules}: {message}")
