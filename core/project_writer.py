from pathlib import Path

def write_project(files: dict, base_path: Path):
    for relative_path, content in files.items():
        file_path = base_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
