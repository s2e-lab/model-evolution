"""
Creates a JSON file with the metadata of the models from the Hugging Face API.
The metadata includes information such as the model's name, description, tags, and the number of likes and downloads.
The models are sorted by the number of likes or downloads. The JSON file is saved in the `results` directory.
@Author: Joanna C. S. Santos (joannacss@nd.edu)
"""
import json
import time
import zipfile
from pathlib import Path

from analyticaml.model_download import get_models_metadata
from huggingface_hub import HfApi
from tqdm import tqdm


def save(models_list: list, out_file: Path) -> None:
    """
    This function saves the models metadata to a JSON file and compresses it.
    :param models_list:  list of models metadata
    :param out_file: path to the output file
    """
    print(f"Saving {len(models_list)} models metadata")
    with open(out_file, "w") as outfile:
        outfile.write(json.dumps(models_list, indent=2, default=str))
    # Compress the file
    with zipfile.ZipFile(out_file.with_suffix(".json.zip"), 'w', compression=zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.write(out_file, arcname=out_file.name)

    # Delete the uncompressed file
    out_file.unlink()


if __name__ == '__main__':
    print("Getting models from Hugging Face API...")
    # Configure what  models to get from the Hugging Face API
    total = None  # if None, it will retrieve all models
    sorting_criteria = "createdAt"  # "downloads" "likes"
    full = True  # whether to get the full model information (true) or not (false)
    sort_direction = True  # True for ascending, False for descending

    # Retrieve the models
    start = time.perf_counter()
    models = get_models_metadata(sorting_criteria, total, full, sort_direction)
    models = [m for m in models if m.created_at.year <= 2024]  # skips models created after 2024
    print(f"Found {len(models)} models in {(time.perf_counter() - start):.4f} seconds created on or before 2024")

    # Parse the retrieved metadata
    results = []
    api = HfApi()
    print("Parsing models metadata...")
    output_file = Path(f"../data/hf_sort_by_{sorting_criteria}_top{len(models)}.json")
    for model_metadata in tqdm(models):
        results.append(vars(model_metadata))
        # Get the model files
        repo_files = []
        if model_metadata.siblings:
            for sibling in model_metadata.siblings:
                repo_file = vars(sibling)
                repo_file["extension"] = repo_file["rfilename"].rsplit(".", 2)[-1]
                repo_files.append(repo_file)

        results[-1]["siblings"] = repo_files

    # Save the results as a zip file
    save(results, output_file)

    print("Done!")
    print("You can find the results in the data folder.")
    print("Recommended: run the tests on tests/test_get_models.py to check the results.")
    print(f"Output file: {output_file.with_suffix('.json.zip')}")
