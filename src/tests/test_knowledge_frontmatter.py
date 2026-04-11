import pytest

from app.service.knowledge_frontmatter import KEYS_PREFIX, detect_file_type, generate

# -- detect_file_type --


def test_detect_file_type_md():
    assert detect_file_type("notes.md") == "md"


def test_detect_file_type_txt():
    assert detect_file_type("readme.txt") == "txt"


def test_detect_file_type_json():
    assert detect_file_type("config.json") == "json"


def test_detect_file_type_yml():
    assert detect_file_type("data.yml") == "yml"


def test_detect_file_type_invalid_raises():
    with pytest.raises(ValueError, match="Unsupported file type"):
        detect_file_type("script.py")


def test_detect_file_type_no_extension_raises():
    with pytest.raises(ValueError):
        detect_file_type("Makefile")


# -- generate: md --


def test_generate_md_uses_h1_as_name():
    name, _, _ = generate("file.md", "# My Document\n\nSome content.", "md")
    assert name == "My Document"


def test_generate_md_falls_back_to_stem_when_no_heading():
    name, _, _ = generate("my_notes.md", "Just some text.", "md")
    assert name == "my notes"


def test_generate_md_description_is_first_non_heading_line():
    _, desc, _ = generate("file.md", "# Title\n\nFirst paragraph.", "md")
    assert desc == "First paragraph."


def test_generate_md_tags_from_headings():
    content = "# Title\n\n## Section One\n\n### Sub\n"
    _, _, tags = generate("file.md", content, "md")
    assert "title" in tags
    assert "section-one" in tags


def test_generate_md_empty_content():
    name, desc, tags = generate("my_file.md", "", "md")
    assert name == "my file"
    assert desc == ""
    assert tags == []


# -- generate: txt --


def test_generate_txt_name_from_stem():
    name, _, _ = generate("my-doc.txt", "Hello world", "txt")
    assert name == "my doc"


def test_generate_txt_description_is_first_line():
    _, desc, _ = generate("file.txt", "First line\nSecond line", "txt")
    assert desc == "First line"


def test_generate_txt_tags_always_text():
    _, _, tags = generate("file.txt", "anything", "txt")
    assert tags == ["text"]


def test_generate_txt_empty_content():
    name, desc, tags = generate("file.txt", "", "txt")
    assert name == "file"
    assert desc == ""
    assert tags == ["text"]


# -- generate: json --


def test_generate_json_name_from_name_key():
    name, _, _ = generate("data.json", '{"name": "My Config", "version": "1.0"}', "json")
    assert name == "My Config"


def test_generate_json_description_lists_keys():
    _, desc, _ = generate("data.json", '{"name": "X", "version": "1.0"}', "json")
    assert desc.startswith(KEYS_PREFIX)
    assert "version" in desc


def test_generate_json_tags_are_top_keys():
    _, _, tags = generate("data.json", '{"alpha": 1, "beta": 2}', "json")
    assert "alpha" in tags
    assert "beta" in tags


def test_generate_json_invalid_falls_back():
    name, desc, tags = generate("broken.json", "not json {{", "json")
    assert name == "broken"
    assert desc == ""
    assert tags == []


# -- generate: yml --


def test_generate_yml_name_from_name_key():
    name, _, _ = generate("config.yml", "name: My Service\nport: 8080", "yml")
    assert name == "My Service"


def test_generate_yml_description_lists_keys():
    _, desc, _ = generate("config.yml", "name: X\nport: 8080", "yml")
    assert desc.startswith(KEYS_PREFIX)
    assert "port" in desc


def test_generate_yml_invalid_falls_back():
    name, desc, tags = generate("bad.yml", ": !!invalid", "yml")
    assert name == "bad"
    assert desc == ""
    assert tags == []
