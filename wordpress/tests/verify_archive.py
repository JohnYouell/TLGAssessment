from pathlib import Path
from zipfile import ZipFile

root = Path(__file__).resolve().parents[1]
expected = {
    "tlg-assessments/tlg-assessments.php",
    "tlg-assessments/includes/core.php",
    "tlg-assessments/includes/accounts.php",
    "tlg-assessments/includes/content-payments.php",
    "UPDATE-INSTRUCTIONS.md",
}
with ZipFile(root / "downloads/TLG-Assessments-1.0.1-FILE-UPDATE.zip") as archive:
    assert set(archive.namelist()) == expected, "Unexpected archive contents"
    assert archive.testzip() is None, "Archive CRC verification failed"
    for name in expected:
        assert archive.read(name) == (root / name).read_bytes(), f"Source mismatch: {name}"
print("Download ZIP verified: all five entries exactly match the tested source.")
