"""
Creates a JSON file with the metadata of the models from the Hugging Face API.
The metadata includes information such as the model's name, description, tags, and the number of likes and downloads.
The models are sorted by the number of likes or downloads. The JSON file is saved in the `results` directory.
@Author: Joanna C. S. Santos (joannacss@nd.edu)
"""
import json
import zipfile
import time
from pathlib import Path

from analyticaml.model_download import get_models_metadata
from huggingface_hub import HfApi
from tqdm import tqdm

if __name__ == '__main__':
    print("Getting models from Hugging Face API...")
    # Configure what  models to get from the Hugging Face API
    total = None  # if None, it will retrieve all models
    sorting_criteria = "createdAt"  # "downloads" "likes"
    full = False  # whether to get the full model information (true) or not (false)
    sort_direction = True  # True for ascending, False for descending

    # Retrieve the models
    start = time.perf_counter()
    models = get_models_metadata(sorting_criteria, total, full, sort_direction)
    print(f"Downloaded {len(models)} models in {(time.perf_counter() - start):.4f} seconds")

    # Parse the retrieved metadata
    results = []

    # Used to get the model information in more details (e.g. siblings' size and total repo size)
    api = HfApi()
    for model in tqdm(models):
        # skips models created after 2024
        if model.created_at.year > 2024: continue

        if model.gated:  # if it is gated, don't try to get the model info (we cant anyway!)
            results.append(vars(model))
        else:  # if it is not gated, get the model info to include repo size and files' sizes
            model_info = api.model_info(model.id, revision=model.sha, files_metadata=True)
            results.append(vars(model_info))
            # Get the model files
            repo_files = []
            if model_info.siblings:
                for sibling in model_info.siblings:
                    repo_file = vars(sibling)
                    repo_file["extension"] = repo_file["rfilename"].rsplit(".", 2)[-1]
                    repo_files.append(repo_file)

            results[-1]["siblings"] = repo_files

    # Save the results as a zip file
    print("Saving  results")

    output_file = Path(f"../data/hf_sort_by_{sorting_criteria}_top{len(results)}.json")
    with open(output_file, "w") as outfile:
        outfile.write(json.dumps(results, indent=2, default=str))

    # Compress the file
    with zipfile.ZipFile(output_file.with_suffix(".json.zip"), 'w', compression=zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.write(output_file, arcname=output_file.name)

    # Delete the uncompressed file
    output_file.unlink()

    print("Done!")
