from __future__ import annotations

import json

import pytest

from lexdays.cli import main


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def test_deadline_text_tr(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "deadline", "tr/hmk", "2026-07-30", "P2W", "--lang", "tr")
    assert code == 0
    assert "Son gün: 08.09.2026 Salı" in out
    assert "[HMK m.102 ve m.104]" in out


def test_deadline_json_with_options_and_backwards(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(
        capsys, "deadline", "us/frcp", "2025-09-15", "P14D", "--before", "--json",
        "-o", "filing=paper", "-o", "observed_friday=not_holiday",
    )
    assert code == 0
    data = json.loads(out)
    assert data["deadline"] == "2025-08-29"
    assert data["direction"] == "before"
    assert data["options"]["filing"] == "paper"


def test_option_values_are_typed(capsys: pytest.CaptureFixture[str]) -> None:
    code, _, err = run(capsys, "deadline", "tr/hmk", "2026-07-30", "P2W", "-o", "judicial_recess=true")
    assert code == 1
    assert "must be one of" in err


def test_bad_option_syntax_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["deadline", "tr/hmk", "2026-07-30", "P2W", "-o", "nonsense"])
    assert exc.value.code == 2


def test_holidays_text_and_kinds(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "holidays", "tr", "2026", "--lang", "tr")
    assert code == 0
    assert "Kurban Bayramı" in out
    assert "(from 13:00)" in out
    code, out, _ = run(capsys, "holidays", "us", "2026", "--kind", "observed_friday", "--json")
    assert json.loads(out)[0]["date"] == "2026-07-03"


def test_add_between_check(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, "add", "tr", "2026-05-22", "3", "--json")[1].strip() == '{\n  "date": "2026-06-01"\n}'
    assert run(capsys, "between", "tr", "2026-05-22", "2026-06-01")[1].strip() == "3"
    assert run(capsys, "check", "tr", "2026-05-27", "--lang", "tr")[1].strip() == "Kurban Bayramı"
    assert run(capsys, "check", "tr", "2026-05-23")[1].strip() == "weekend"
    assert run(capsys, "check", "tr", "2026-05-23", "--lang", "tr")[1].strip() == "hafta sonu"
    assert run(capsys, "check", "tr", "2026-05-22")[1].strip() == "business day"
    assert run(capsys, "check", "tr", "2026-05-22", "--lang", "tr")[1].strip() == "iş günü"


def test_check_answers_in_every_language(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, "check", "de", "2026-05-22", "--lang", "de")[1].strip() == "Arbeitstag"
    assert run(capsys, "check", "de", "2026-05-23", "--lang", "fr")[1].strip() == "week-end"
    assert run(capsys, "check", "tr", "2026-05-22", "--lang", "ja")[1].strip() == "営業日"


def test_deadline_uses_the_court_seat_calendar(capsys: pytest.CaptureFixture[str]) -> None:
    # 8 August (Friedensfest) is a holiday only in the city of Augsburg.
    def deadline(cal: str) -> str:
        out = run(capsys, "deadline", "de/zpo", "2025-07-25", "P2W", "--calendar", cal, "--json")[1]
        return str(json.loads(out)["deadline"])

    assert (deadline("de-by-catholic"), deadline("de-by-augsburg")) == ("2025-08-08", "2025-08-11")


def test_list(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "list")
    assert code == 0
    assert "tr/hmk" in out
    assert "de-by-catholic" in out
    data = json.loads(run(capsys, "list", "--json")[1])
    assert {p["id"] for p in data["rulepacks"]} >= {"tr/hmk", "us/frcp", "gb-eaw/cpr", "eu/cj", "de/zpo"}


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["deadline", "tr/hmk", "2026-02-30", "P2W"], "not a valid date"),
        (["deadline", "nope/pack", "2026-02-02", "P2W"], "unknown rule pack"),
        (["holidays", "tr", "2040"], "verified holiday data"),
        (["deadline", "tr/hmk", "2026-02-02", "2 fortnights"], "cannot parse period"),
    ],
)
def test_errors_exit_with_code_1(capsys: pytest.CaptureFixture[str], args: list[str], message: str) -> None:
    code, _, err = run(capsys, *args)
    assert code == 1
    assert message in err


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "lexdays" in capsys.readouterr().out
