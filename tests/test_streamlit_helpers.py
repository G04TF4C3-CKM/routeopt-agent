import os
from pathlib import Path

def test_list_sample_files_exists():
    # Import the helper from the streamlit app (module-level function)
    from streamlit_app import _list_sample_files
    files = _list_sample_files()
    # There should be at least one .txt file in the data directory
    assert isinstance(files, list)
    assert len(files) > 0
    for f in files:
        assert isinstance(f, Path)
        assert f.suffix == ".txt"
        assert f.is_file()
