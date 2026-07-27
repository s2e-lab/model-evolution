import json


def merge_json(file1: str, file2: str, output: str) -> None:
    with open(file1, "r") as f:
        data1 = json.load(f)

    with open(file2, "r") as f:
        data2 = json.load(f)

    data1.update(data2)  # file2 overwrites duplicate keys

    with open(output, "w") as f:
        json.dump(data1, f, indent=2)


if __name__ == "__main__":
    merge_json(
        "_repo_size_cache.json",
        "_repo_size_cache_bottom.json",
        "repo_size_cache_merged.json",
    )