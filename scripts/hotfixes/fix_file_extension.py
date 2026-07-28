import zipfile

from utils import load, get_file_extension, DATA_DIR

INPUT =  DATA_DIR / "hf_sort_by_createdAt_top1209240.json.zip"
OUTPUT = INPUT.with_stem(INPUT.stem + "_fixed")

print("Loading models")
df = load(INPUT)

print("Fixing models")
for siblings in df["siblings"]:
    for sibling in siblings:
        old_extension = sibling["extension"]
        sibling["extension"] = get_file_extension(sibling["rfilename"])
        assert old_extension == sibling["extension"] or sibling["extension"] == ""

print("Saving models")
df.to_json(OUTPUT.with_suffix(".json"), orient="records", indent=2)
with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.write(OUTPUT.with_suffix(".json"), arcname=INPUT.with_suffix("").name)
OUTPUT.with_suffix(".json").unlink()