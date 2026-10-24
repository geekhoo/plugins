"""c0-wordstat hidden oracle (W1-W11 in spec.md)."""
import json

from conftest import SAMPLE, SAMPLE_JSON_TOP2, SAMPLE_TEXT, assert_error, assert_ok, assert_usage


def test_w1_help(run):
    res = run("--help")
    assert_ok(res)
    assert res.out


def test_w2_example_text(run, write):
    res = run(write("sample.txt", SAMPLE))
    assert_ok(res)
    assert res.out == SAMPLE_TEXT


def test_w3_example_json_top2(run, write):
    res = run("--json", "--top", "2", write("sample.txt", SAMPLE))
    assert_ok(res)
    assert res.out == SAMPLE_JSON_TOP2


def test_w4_default_top_is_three(run, write):
    res = run("--json", write("sample.txt", SAMPLE))
    assert_ok(res)
    assert [t["word"] for t in json.loads(res.out)["top"]] == ["cat", "the", "a"]


def test_w5_ties_by_word_and_top_above_distinct(run, write):
    res = run("--top", "10", write("t.txt", "b a c b a c d\n"))
    assert_ok(res)
    assert res.out.splitlines()[-1] == "top: a=2 b=2 c=2 d=1"


def test_w6_tokens_lowercase_digits_split_on_other(run, write):
    res = run("--json", "--top", "5", write("t.txt", "R2-D2 r2d2 R2 don't Éclair"))
    assert_ok(res)
    data = json.loads(res.out)
    # tokens: r2 d2 r2d2 r2 don t clair
    assert data["words"] == 7 and data["lines"] == 1 and data["chars"] == 26
    assert data["top"][0] == {"word": "r2", "count": 2}
    assert [t["word"] for t in data["top"][1:]] == ["clair", "d2", "don", "r2d2"]


def test_w7_empty_file(run, write):
    path = write("empty.txt", b"")
    res = run(path)
    assert_ok(res)
    assert res.out == "lines: 0\nwords: 0\nchars: 0\ntop:\n"
    res = run("--json", path)
    assert_ok(res)
    assert res.out == '{"lines": 0, "words": 0, "chars": 0, "top": []}\n'


def test_w8_bom_and_crlf(run, write):
    res = run(write("bom.txt", b"\xef\xbb\xbfone two\r\ntwo\r\n"))
    assert_ok(res)
    assert res.out == "lines: 2\nwords: 3\nchars: 14\ntop: two=2 one=1\n"


def test_w9_missing_file(run, tmp_path):
    missing = tmp_path / "nope.txt"
    assert_error(run(missing), f"{missing}: cannot read file")


def test_w9_directory(run, tmp_path):
    assert_error(run(tmp_path), f"{tmp_path}: cannot read file")


def test_w9_invalid_utf8(run, write):
    path = write("bad.txt", b"ok \xff\xfe bad\n")
    assert_error(run(path), f"{path}: not valid UTF-8")


def test_w10_usage_errors(run, write):
    path = write("sample.txt", SAMPLE)
    assert_usage(run("--top", "0", path))
    assert_usage(run("--top", "x", path))
    assert_usage(run())


def test_w11_deterministic_no_cr(run, write):
    path = write("sample.txt", "x y\r\nx\n")
    first, second = run(path), run("--json", path)
    assert_ok(first)
    assert_ok(second)
    assert b"\r" not in first.raw_out + second.raw_out
    assert run(path).raw_out == first.raw_out
