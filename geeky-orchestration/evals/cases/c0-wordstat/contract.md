# wordstat: Interface Contract

## Constraints

- **Stack:** Python >=3.11, standard library only; pytest for tests only.
- **Package location:** `wordstat/` at repo root (flat layout, no `src/`).
- **Entry point:** `python -m wordstat ...` run from repo root.

## Functional requirements

- **R1** `python -m wordstat --help` exits 0.
- **R2** `python -m wordstat [--json] [--top N] FILE` reads exactly one file, decoded as UTF-8 with an optional BOM (`utf-8-sig`). stdin is never read.
- **R3** Counts, computed on the decoded text:
  - `lines` = `len(text.splitlines())`
  - `words` = number of matches of `[a-z0-9]+` in `text.lower()`
  - `chars` = `len(text)` (code points, BOM excluded)
- **R4** `top` lists the `N` most frequent words (same tokens as R3), ordered by count descending, then word ascending. `--top` defaults to 3. Fewer than `N` distinct words lists all of them.
- **R5** Default output is the text format; `--json` selects the JSON format.
- **R6** Output is deterministic: UTF-8, `\n` line endings, no locale use. stdout is reconfigured to `encoding="utf-8", newline="\n"`.

## Interface contract

### Command

```
python -m wordstat [--json] [--top N] FILE
```

- argparse `prog` is `wordstat`.
- `--top` must be an integer >= 1, else usage error.

### Text format

Exactly four lines, each ending in `\n`:

```
lines: <lines>
words: <words>
chars: <chars>
top: <word>=<count> <word>=<count> ...
```

With no words, the last line is `top:` with no trailing space.

### JSON format

One line: the result of `json.dumps(obj)` with default separators, followed by `\n`, where `obj` has keys in this order:

```
{"lines": <int>, "words": <int>, "chars": <int>, "top": [{"word": <str>, "count": <int>}, ...]}
```

### Exit codes and errors

Errors print one line to stderr, prefix `wordstat: error: `, and leave stdout empty. `<path>` is the FILE argument exactly as given.

| Condition | Exit | stderr (after prefix) |
|---|---|---|
| File missing, a directory, or unreadable | 3 | `<path>: cannot read file` |
| Not valid UTF-8 | 3 | `<path>: not valid UTF-8` |
| Usage error (missing FILE, unknown flag, bad `--top`) | 2 | argparse default; the last stderr line must match `^wordstat: error: ` |

Exit 0 on success, including an empty file. Exit 1 is reserved for unexpected internal errors.

## Example

`sample.txt` (UTF-8, `\n` endings):

```
The cat sat.
The cat ran!
A dog.
```

`python -m wordstat sample.txt` → exit 0, stdout:

```
lines: 3
words: 8
chars: 33
top: cat=2 the=2 a=1
```

`python -m wordstat --json --top 2 sample.txt` → exit 0, stdout:

```
{"lines": 3, "words": 8, "chars": 33, "top": [{"word": "cat", "count": 2}, {"word": "the", "count": 2}]}
```
