import locale
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_wordstat(*args, env=None, cwd=None, input=None):
    child_env = os.environ.copy()
    if env is not None:
        child_env.update(env)
    search_path = [str(REPO_ROOT)]
    if child_env.get("PYTHONPATH"):
        search_path.append(child_env["PYTHONPATH"])
    child_env["PYTHONPATH"] = os.pathsep.join(search_path)
    return subprocess.run(
        [sys.executable, "-m", "wordstat", *map(str, args)],
        capture_output=True,
        cwd=cwd or REPO_ROOT,
        env=child_env,
        input=input,
    )


def test_help():
    result = run_wordstat("--help")
    assert result.returncode == 0
    assert b"usage: wordstat" in result.stdout
    assert result.stderr == b""


def test_contract_example_text_and_json(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_bytes(b"The cat sat.\nThe cat ran!\nA dog.\n")

    text = run_wordstat(sample)
    assert text.returncode == 0
    assert text.stderr == b""
    assert text.stdout == b"lines: 3\nwords: 8\nchars: 33\ntop: cat=2 the=2 a=1\n"

    result = run_wordstat("--json", "--top", 2, sample)
    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == (
        b'{"lines": 3, "words": 8, "chars": 33, '
        b'"top": [{"word": "cat", "count": 2}, {"word": "the", "count": 2}]}\n'
    )


def test_bom_is_excluded_from_character_count(tmp_path):
    sample = tmp_path / "bom.txt"
    sample.write_bytes(b"\xef\xbb\xbfCat\n")

    result = run_wordstat(sample)

    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == b"lines: 1\nwords: 1\nchars: 4\ntop: cat=1\n"


def test_crlf_code_points_are_preserved_for_character_count(tmp_path):
    sample = tmp_path / "crlf.txt"
    sample.write_bytes(b"A\r\nB\r\n")

    result = run_wordstat(sample)

    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == b"lines: 2\nwords: 2\nchars: 6\ntop: a=1 b=1\n"


def test_empty_file_has_exact_empty_summary(tmp_path):
    sample = tmp_path / "empty.txt"
    sample.write_bytes(b"")

    result = run_wordstat(sample)

    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == b"lines: 0\nwords: 0\nchars: 0\ntop:\n"


def test_no_tokens_has_top_line_without_trailing_space(tmp_path):
    sample = tmp_path / "punctuation.txt"
    sample.write_bytes(b"!?!\n")

    result = run_wordstat(sample)

    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == b"lines: 1\nwords: 0\nchars: 4\ntop:\n"


def test_ties_are_lexical_and_large_top_lists_available_words(tmp_path):
    sample = tmp_path / "ties.txt"
    sample.write_bytes(b"z y x z y x\n")

    result = run_wordstat("--top", 8, sample)

    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == b"lines: 1\nwords: 6\nchars: 12\ntop: x=2 y=2 z=2\n"


def test_stdout_is_explicitly_configured_for_utf8_lf():
    with open("wordstat/__main__.py", encoding="utf-8") as source:
        code = source.read()
    assert 'sys.stdout.reconfigure(encoding="utf-8", newline="\\n")' in code
    assert "locale" not in code.lower()


def test_output_is_independent_of_locale_when_alternate_is_available(tmp_path):
    sample = tmp_path / "locale.txt"
    sample.write_bytes(b"A cat\nA dog\n")
    baseline = run_wordstat(sample)
    assert baseline.returncode == 0

    current = locale.setlocale(locale.LC_ALL)
    alternatives = ["C", "C.UTF-8", "POSIX", "en_US.UTF-8"]
    other = next(
        (
            candidate
            for candidate in alternatives
            if candidate.lower() != current.lower()
            and subprocess.run(
                [sys.executable, "-c", "import locale; locale.setlocale(locale.LC_ALL)"],
                capture_output=True,
                env={**os.environ, "LC_ALL": candidate},
            ).returncode
            == 0
        ),
        None,
    )
    if other is None:
        return

    result = run_wordstat(sample, env={**os.environ, "LC_ALL": other})
    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == baseline.stdout


def test_unicode_lowercase_codepoints_and_splitlines_boundaries(tmp_path):
    text = "İ Aİ ẞSTRAẞE KK １２３\r\nx\u2028y\v z\f"
    sample = tmp_path / "unicode.txt"
    sample.write_bytes(text.encode("utf-8"))

    tokens = re.findall(r"[a-z0-9]+", text.lower())
    counts = Counter(tokens)
    top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:3]
    expected = (
        f"lines: {len(text.splitlines())}\n"
        f"words: {len(tokens)}\n"
        f"chars: {len(text)}\n"
        f"top: {' '.join(f'{word}={count}' for word, count in top)}\n"
    ).encode("utf-8")

    result = run_wordstat(sample)

    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == expected


def assert_usage_error(result):
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr
    assert b"Traceback" not in result.stderr
    assert re.search(rb"^wordstat: error: ", result.stderr.splitlines()[-1])


@pytest.mark.parametrize("top", ["not-an-integer", "1.5", "0", "-1"])
def test_invalid_top_is_usage_error(tmp_path, top):
    sample = tmp_path / "input.txt"
    sample.write_text("content", encoding="utf-8")

    assert_usage_error(run_wordstat("--top", top, sample))


@pytest.mark.parametrize(
    "arguments",
    [
        (),
        ("--unknown", "input.txt"),
        ("input.txt", "extra.txt"),
    ],
)
def test_invalid_command_shape_is_usage_error(tmp_path, arguments):
    (tmp_path / "input.txt").write_text("content", encoding="utf-8")

    assert_usage_error(run_wordstat(*arguments, cwd=tmp_path))


def test_missing_file_uses_exact_supplied_path_in_error(tmp_path):
    result = run_wordstat("missing.txt", cwd=tmp_path)

    assert result.returncode == 3
    assert result.stdout == b""
    assert result.stderr == b"wordstat: error: missing.txt: cannot read file\n"
    assert b"Traceback" not in result.stderr


def test_directory_uses_exact_supplied_path_in_error(tmp_path):
    (tmp_path / "sample-dir").mkdir()

    result = run_wordstat("sample-dir", cwd=tmp_path)

    assert result.returncode == 3
    assert result.stdout == b""
    assert result.stderr == b"wordstat: error: sample-dir: cannot read file\n"
    assert b"Traceback" not in result.stderr


def test_unreadable_regular_file_uses_exact_supplied_path_in_error(tmp_path):
    sample = tmp_path / "unreadable.txt"
    sample.write_text("content", encoding="utf-8")
    original_mode = sample.stat().st_mode
    sample.chmod(0)
    try:
        try:
            with sample.open("rb"):
                pass
        except OSError:
            pass
        else:
            pytest.skip("host process/filesystem can still read a mode-000 file")

        result = run_wordstat("unreadable.txt", cwd=tmp_path)
    finally:
        sample.chmod(original_mode)

    assert result.returncode == 3
    assert result.stdout == b""
    assert result.stderr == b"wordstat: error: unreadable.txt: cannot read file\n"
    assert b"Traceback" not in result.stderr


def test_invalid_utf8_uses_exact_supplied_path_in_error(tmp_path):
    (tmp_path / "invalid.txt").write_bytes(b"valid prefix \xff invalid suffix")

    result = run_wordstat("invalid.txt", cwd=tmp_path)

    assert result.returncode == 3
    assert result.stdout == b""
    assert result.stderr == b"wordstat: error: invalid.txt: not valid UTF-8\n"
    assert b"Traceback" not in result.stderr


def test_stdin_without_file_remains_usage_error(tmp_path):
    assert_usage_error(run_wordstat(cwd=tmp_path, input=b"stdin must not be read\n"))
