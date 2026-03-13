"""Tests for termui.theme module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from termui.theme import (
    Theme,
    ThemeConfig,
    apply_theme,
    current,
    current_theme_name,
    get_theme,
    list_themes,
    load_theme,
    register_theme,
    save_theme,
    theme_context,
)


# ── ThemeConfig serialization ────────────────────────────────────────

def test_to_dict_round_trip():
    cfg = ThemeConfig(success="bold magenta")
    d = cfg.to_dict()
    cfg2 = ThemeConfig.from_dict(d)
    assert cfg2.success == "bold magenta"


def test_from_dict_ignores_unknown_keys():
    cfg = ThemeConfig.from_dict({"success": "bold blue", "unknown_key": "value"})
    assert cfg.success == "bold blue"


# ── apply_theme ──────────────────────────────────────────────────────

def test_apply_theme_enum():
    apply_theme(Theme.LIGHT)
    assert current_theme_name() == "light"
    assert current().success == "bold dark_green"


def test_apply_theme_string():
    apply_theme("monokai")
    assert current_theme_name() == "monokai"


def test_apply_theme_config():
    cfg = ThemeConfig(success="bold #ff0000")
    apply_theme(cfg)
    assert current().success == "bold #ff0000"
    assert current_theme_name() == "<custom>"


def test_apply_theme_bad_type():
    with pytest.raises(TypeError):
        apply_theme(42)  # type: ignore[arg-type]


def test_apply_theme_unknown_string():
    with pytest.raises(KeyError):
        apply_theme("nonexistent")


# ── register / get ───────────────────────────────────────────────────

def test_register_and_get():
    register_theme("ocean", ThemeConfig(info="bold #00bfff"))
    cfg = get_theme("ocean")
    assert cfg.info == "bold #00bfff"


def test_register_builtin_name_raises():
    with pytest.raises(ValueError):
        register_theme("dark", ThemeConfig())


def test_get_theme_builtin():
    cfg = get_theme("dark")
    assert cfg.success == "bold green"


def test_get_theme_unknown():
    with pytest.raises(KeyError):
        get_theme("does_not_exist")


# ── list_themes ──────────────────────────────────────────────────────

def test_list_themes_contains_builtins():
    names = list_themes()
    for builtin in ["dark", "light", "monokai", "solarized", "plain"]:
        assert builtin in names


def test_list_themes_sorted():
    names = list_themes()
    assert names == sorted(names)


# ── theme_context ────────────────────────────────────────────────────

def test_theme_context_restores():
    apply_theme(Theme.DARK)
    with theme_context(Theme.LIGHT):
        assert current_theme_name() == "light"
    assert current_theme_name() == "dark"


def test_theme_context_restores_on_error():
    apply_theme(Theme.DARK)
    with pytest.raises(RuntimeError):
        with theme_context(Theme.MONOKAI):
            assert current_theme_name() == "monokai"
            raise RuntimeError("boom")
    assert current_theme_name() == "dark"


# ── save / load ──────────────────────────────────────────────────────

def test_save_and_load(tmp_path: Path):
    cfg = ThemeConfig(success="bold #abcdef")
    path = tmp_path / "theme.json"
    save_theme(cfg, path)
    loaded = load_theme(path)
    assert loaded.success == "bold #abcdef"


def test_saved_file_is_valid_json(tmp_path: Path):
    path = tmp_path / "theme.json"
    save_theme(ThemeConfig(), path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "success" in data
