"""
Creates a JSON file with the metadata of the models from the Hugging Face API.
The metadata includes information such as the model's name, description, tags, and the number of likes and downloads.
The models are sorted by the number of likes or downloads. The JSON file is saved in the `results` directory.
@Author: Joanna C. S. Santos (joannacss@nd.edu)
"""
import csv
import json
from pathlib import Path

from analyticaml import MODEL_FILE_EXTENSIONS
from analyticaml.model_download import get_models_metadata

if __name__ == '__main__':
    print("Getting models from Hugging Face API...")
    # Configure what  models to get from the Hugging Face API
    total = None  # if None, it will retrieve all models
    sorting_criteria = "createdAt"  # #"downloads"  # "likes" #
    full = True  # whether to get the full model information (true) or not (false)
    sort_direction = False  # True for ascending, False for descending
    # Retrieve the models
    models = get_models_metadata(sorting_criteria, total, full, sort_direction)
    # Parse
    results = []
    print("Downloaded", len(models), "models")
    for model in models:
        results.append(vars(model))

    if not total: total = len(results)

    # Save the results
    print("Saving results")
    results_dict = {"results": results}
    output_file = Path(f"../results/huggingface_sort_by_{sorting_criteria}_top{total}.json")
    with open(output_file, "w") as outfile:
        outfile.write(json.dumps(results_dict, indent=2, default=str))

    # output csv is the same as the json file, but in csv format and with a suffix _model_files_filtered
    output_csv = output_file.with_name(output_file.stem + "_model_files_filtered.csv")
    with open(output_csv, "w") as f:
        csv_writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        csv_writer.writerow(["repo", "model_file", "extension"])
        for model in results_dict["results"]:
            siblings = model.get("siblings", [])

            if siblings:
                for file in siblings:
                    extension = file.rfilename.rsplit(".", 2)[-1]
                    if extension in MODEL_FILE_EXTENSIONS:
                        csv_writer.writerow([model["modelId"], file.rfilename, extension])

    print("Saved results to", output_csv)
