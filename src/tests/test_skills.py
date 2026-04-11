import math
import tempfile
from pathlib import Path

from app.agents.skills.calculator.tools import calculate
from app.agents.skills.file_ops.tools import list_directory, read_file
from app.agents.skills.loader import build_skill_catalog, load_skill
from app.agents.skills.web_search.tools import MOCK_RESULTS, search_web
from app.shared.field_keys import FIELD_KEY_DESCRIPTION, FIELD_KEY_NAME

# -- calculate --


def test_calculate_addition():
    result = calculate.invoke({"expression": "2 + 3"})
    assert result == "5"


def test_calculate_multiplication():
    result = calculate.invoke({"expression": "6 * 7"})
    assert result == "42"


def test_calculate_sqrt():
    result = calculate.invoke({"expression": "sqrt(16)"})
    assert result == "4.0"


def test_calculate_trig_sin():
    result = calculate.invoke({"expression": "sin(0)"})
    assert result == "0.0"


def test_calculate_trig_cos():
    result = calculate.invoke({"expression": "cos(0)"})
    assert result == "1.0"


def test_calculate_uses_pi():
    result = calculate.invoke({"expression": "round(pi, 5)"})
    assert result == str(round(math.pi, 5))


def test_calculate_invalid_expression_returns_error():
    result = calculate.invoke({"expression": "import os"})
    assert "Error" in result


def test_calculate_division_by_zero_returns_error():
    result = calculate.invoke({"expression": "1 / 0"})
    assert "Error" in result


def test_calculate_undefined_name_returns_error():
    result = calculate.invoke({"expression": "open('/etc/passwd')"})
    assert "Error" in result


# -- search_web --


def test_search_web_returns_results():
    results = search_web.invoke({"query": "python testing"})
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_web_result_has_title():
    results = search_web.invoke({"query": "test"})
    assert "title" in results[0]


def test_search_web_result_has_url():
    results = search_web.invoke({"query": "test"})
    assert "url" in results[0]


def test_search_web_result_has_snippet():
    results = search_web.invoke({"query": "test"})
    assert "snippet" in results[0]


def test_search_web_returns_mock_results():
    results = search_web.invoke({"query": "anything"})
    assert results == MOCK_RESULTS


# -- read_file --


def test_read_file_returns_content():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", dir=Path.cwd(), delete=False) as f:
        f.write("hello file")
        tmp_name = Path(f.name).name

    try:
        result = read_file.invoke({"path": tmp_name})
        assert result == "hello file"
    finally:
        (Path.cwd() / tmp_name).unlink(missing_ok=True)


def test_read_file_not_found_returns_message():
    result = read_file.invoke({"path": "nonexistent_file_xyz.txt"})
    assert "not found" in result.lower() or "File not found" in result


def test_read_file_path_traversal_returns_access_denied():
    result = read_file.invoke({"path": "../../../etc/passwd"})
    assert "Access denied" in result


# -- list_directory --


def test_list_directory_returns_sorted_entries():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "b_file.txt").write_text("b")
        (tmp_path / "a_file.txt").write_text("a")
        rel = tmp_path.relative_to(Path.cwd())
        entries = list_directory.invoke({"path": str(rel)})
    assert entries == sorted(entries)


def test_list_directory_includes_created_files():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "test.txt").write_text("hello")
        rel = tmp_path.relative_to(Path.cwd())
        entries = list_directory.invoke({"path": str(rel)})
    assert "test.txt" in entries


def test_list_directory_path_traversal_returns_access_denied():
    entries = list_directory.invoke({"path": "../../../"})
    assert any("Access denied" in e for e in entries)


def test_list_directory_nonexistent_returns_not_a_directory():
    entries = list_directory.invoke({"path": "nonexistent_dir_xyz"})
    assert any("Not a directory" in e for e in entries)


# -- build_skill_catalog --


def test_build_skill_catalog_finds_skills():
    catalog = build_skill_catalog()
    assert len(catalog) > 0


def test_build_skill_catalog_contains_calculator():
    catalog = build_skill_catalog()
    names = [s["name"] for s in catalog]
    assert "calculator" in names


def test_build_skill_catalog_contains_web_search():
    catalog = build_skill_catalog()
    names = [s["name"] for s in catalog]
    assert "web_search" in names


def test_build_skill_catalog_contains_file_ops():
    catalog = build_skill_catalog()
    names = [s["name"] for s in catalog]
    assert "file_ops" in names


def test_build_skill_catalog_entries_have_name_and_description():
    catalog = build_skill_catalog()
    for skill in catalog:
        assert FIELD_KEY_NAME in skill
        assert FIELD_KEY_DESCRIPTION in skill


# -- load_skill --


def test_load_skill_returns_content_for_valid_skill():
    result = load_skill.invoke({"name": "calculator"})
    assert len(result) > 0


def test_load_skill_contains_skill_md_text():
    result = load_skill.invoke({"name": "calculator"})
    assert "calculator" in result.lower() or "math" in result.lower()


def test_load_skill_invalid_name_returns_not_found():
    result = load_skill.invoke({"name": "nonexistent_skill_xyz"})
    assert "not found" in result.lower()
