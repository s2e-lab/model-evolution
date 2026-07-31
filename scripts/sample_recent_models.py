#!/usr/bin/env python
# coding: utf-8
"""
Samples recent model repositories using temporally stratified random sampling.

Each creation quarter receives a minimum allocation, and the remaining sample
is distributed proportionally to the number of repositories in each quarter.

@Author: Joanna C. S. Santos
"""

import random
import pandas as pd
from git import repo

from utils import load, DATA_DIR, calculate_sample_size


def sample(df: pd.DataFrame, seed: int = 42, previous_repos: set | None = None, exclude_repos: set | None = None) -> pd.DataFrame:
    """
    Return a temporally stratified sample.

    For each creation quarter, calculate the required sample size, prioritize
    repositories analyzed previously, and randomly fill any remaining slots.

    :param df: DataFrame to sample from.
    :param seed: Fixed random seed for reproducibility.
    :param previous_repos: Repository identifiers analyzed previously that you'd like to prioritize to pick to avoid re-running everything for cached results.
    :param exclude_repos:  Repositories to exclude from sampling because they are known to fail.
    :return: Sampled DataFrame.
    """
    random.seed(seed)
    previous_repos = previous_repos or set()
    exclude_repos = exclude_repos or set()

    date_col = "created_at"
    repo_col = "id"  # Change to "id" if that is the identifier in df.

    df = df.copy()
    df[date_col] = pd.to_datetime(
        df[date_col],
        utc=True,
        errors="coerce"
    )
    df = df.dropna(subset=[date_col])
    if exclude_repos:
        df = df[~df[repo_col].isin(exclude_repos)]
    print(f"Sampling from {len(df)} repositories...")

    df["quarter"] = df[date_col].dt.tz_localize(None).dt.to_period("Q")

    quarters = sorted(df["quarter"].unique())
    sampled_idx = []

    print("Quarter sampling allocation:")

    for quarter in quarters:
        quarter_df = df[df["quarter"] == quarter]

        population_size = len(quarter_df)
        sample_size = calculate_sample_size(
            population_size,
            margin_error=0.05,
            confidence_level=0.95
        )

        # Previously analyzed repositories in this quarter.
        previous_idx = quarter_df.index[
            quarter_df[repo_col].isin(previous_repos)
        ].tolist()

        # Repositories in this quarter that have not been analyzed.
        remaining_idx = quarter_df.index[
            ~quarter_df[repo_col].isin(previous_repos)
        ].tolist()

        # Randomize both pools reproducibly.
        random.shuffle(previous_idx)
        random.shuffle(remaining_idx)

        # Reuse as many previously analyzed repositories as possible.
        reused_idx = previous_idx[:sample_size]

        # Fill the remaining sample slots with new repositories.
        num_needed = sample_size - len(reused_idx)
        new_idx = random.sample(remaining_idx, num_needed)

        sampled_idx.extend(reused_idx)
        sampled_idx.extend(new_idx)

        print(
            f"{quarter}: population={population_size:,}, "
            f"sample={sample_size:,}, "
            f"reused={len(reused_idx):,}, "
            f"new={len(new_idx):,}"
        )

    sampled_df = df.loc[sorted(sampled_idx)].reset_index(drop=True)
    return sampled_df.drop(columns="quarter")


if __name__ == "__main__":
    input_file = DATA_DIR / "all_recent_repos.json.zip"
    out_recent_models_file = DATA_DIR / "selected_recent_repos.json"

    # Step 1: Load the repositories' metadata.
    print(f"Loading recent repository data from {input_file.name}...")
    df = load(input_file)

    # Step 1.1: When we need to retry from where we stopped to grab more samples after some failed
    # we load the previous ones such that we can ensure they are still selected again
    df_previous = pd.read_json(DATA_DIR / "selected_recent_repos.json")
    previous_repos = set(df_previous["id"].tolist())
    print(f"Found {len(previous_repos)} previous repositories.")
    exclude_repos = {
        "AI-Sweden-Models/gpt-sw3-6.7b-v2",
        "AI-Sweden-Models/gpt-sw3-40b",
        "AkshayPM/t5base-fine-tuned",
        "besimray/miner_id_3_794df6f6-b398-448d-8972-ec017a83142c_1730836890",
        "CHShakish/my-pet-dog",
        "digiplay/YabaLMixAnimeRealistic_V1.0",
        "dzanbek/ac4d17d9-5346-4e15-b45c-46285cf7c718",
        "eeeebbb2/fb074c61-11a3-4256-bf44-f870513053c6",
        "EmbeddedLLM/Phi-3-vision-128k-instruct-onnx",
        "fayetitchenal/segformer_finetuned_test_110424",
        "FoodDesert/Boring_Embeddings",
        "iamanaiart/LCM-hardcoreHentai13_v13Baked-openvino",
        "immich-app/ViT-L-14__openai",
        "JaaackXD/Llama-3-70B-Instruct-GGUF",
        "just-dna-seq/GenNet",
        "Kha37lid/khalidouaze",
        "kiupuc/speecht5_tts",
        "Kwai-Kolors/Kolors",
        "LazarusNLP/congen-indobert-base",
        "licyk/sd-embeddings",
        "ll00292007/Stable-diffusion-mode",
        "MadFritz/sac-BipedalWalker-v3",
        "marcogfedozzi/ppo-LunarLander-v2",
        "mattaq/nnUNet-GelGenie-15-Dec-2023",
        "mjmanashti/fingemma-2b-ti",
        "monadical-labs/minecraft-skin-generator",
        "Outimus/models-and-stuff",
        "polyconnect/dqn-SpaceInvadersNoFrameskip-v4",
        "qgallouedec/ppo-EnduroNoFrameskip-v4-3540983129",
        "qgallouedec/ppo-HumanoidBulletEnv-v0-617916820",
        "qgallouedec/ppo-QbertNoFrameskip-v4-3013272349",
        "qgallouedec/qrdqn-LunarLander-v2-3752531572",
        "qgallouedec/sac-Pendulum-v1-3420645740",
        "qgallouedec/td3-Humanoid-v3-2919924285",
        "qgallouedec/td3-Humanoid-v3-3604187374",
        "qgallouedec/td3-Pendulum-v1-2563443305",
        "qgallouedec/trpo-BipedalWalkerHardcore-v3-3280772883",
        "qgallouedec/trpo-Hopper-v3-1699917211",
        "qgallouedec/trpo-Humanoid-v3-1622997425",
        "qgallouedec/trpo-MountainCarContinuous-v0-2747342494",
        "qgallouedec/trpo-Swimmer-v3-3893167513",
        "sartifyllc/African-Cross-Lingua-Embeddings-Model",
        "sololee/sdModels",
        "songhee/rugged-car",
        "SR467/xzg",
        "stablediffusionapi/wand-magic2",
        "tanaka5/models0918",
        "teticio/latent-audio-diffusion-256",
        "thejosango/nuha",
        "tzs/ppo-LunarLander-v2",
        "uni-zhuan/a2c-PandaReachDense-v3",
        "VERSIL91/026600af-ccd9-4b63-966a-939e5dfcccd0",
        "vumichien/ppo-LunarLander-v2",
        "Xenova/bert-base-multilingual-uncased",
        "Xenova/bert-base-uncased",
        "Xenova/convnext-base-224",
        "Xenova/dinov2-large",
        "Xenova/mbart-large-50-many-to-many-mmt",
        "Xenova/mms-lid-4017",
        "Xenova/multi-qa-mpnet-base-dot-v1",
        "Xenova/opus-mt-en-mul",
        "Xenova/opus-mt-uk-en",
        "Zilun/GeoRSCLIP",
        "Zilun/GeoRSSD",
        "BAAI/OPI-Galactica-6.7B",
        "CyberHarem/abukuma_kantaicollection",
        "CyberHarem/akizuki_kantaicollection",
        "CyberHarem/amatsukaze_kantaicollection",
        "CyberHarem/bismarck_azurlane",
        "CyberHarem/downes_azurlane",
        "CyberHarem/eternity_larva_touhou",
        "CyberHarem/ganyu_genshin",
        "CyberHarem/gr_sl8_girlsfrontline",
        "CyberHarem/hamakaze_kantaicollection",
        "CyberHarem/haruka_bluearchive",
        "CyberHarem/hina_bluearchive",
        "CyberHarem/horikawa_raiko_touhou",
        "CyberHarem/hu_tao_genshin",
        "CyberHarem/ise_kantaicollection",
        "CyberHarem/isuzu_azurlane",
        "CyberHarem/ithea_sukasuka",
        "CyberHarem/jintsu_azurlane",
        "CyberHarem/joutougu_mayumi_touhou",
        "CyberHarem/leipzig_azurlane",
        "CyberHarem/maury_azurlane",
        "CyberHarem/midori_bluearchive",
        "CyberHarem/nanaka_neuralcloud",
        "CyberHarem/natsu_bluearchive",
        "CyberHarem/noa_bluearchive",
        "CyberHarem/okunoda_miyoi_touhou",
        "CyberHarem/orchid_arknights",
        "CyberHarem/princeton_azurlane",
        "CyberHarem/rico_girlsfrontline",
        "CyberHarem/rise_neuralcloud",
        "CyberHarem/rurutie_azurlane",
        "CyberHarem/tatsuta_kantaicollection",
        "CyberHarem/toyosatomimi_no_miko_touhou",
        "CyberHarem/vee_neuralcloud",
        "CyberHarem/white_heart_azurlane",
        "LieDeath/MergeStove2.5D",
        "LoftQ/Mistral-7B-v0.1-4bit-64rank",
        "Milim/gmal",
        "OdiaGenAI/odiagenAI-bengali-base-model-v1",
        "SDXR/SDXR-Coll",
        "Xenova/beit-base-patch16-384",
        "Xenova/opus-mt-sv-en",
        "Xenova/vit-gpt2-image-captioning",
        "amandaic1805/MoondropCollection",
        "arodriguez/ppo-LunarLander-v2-colab",
        "closertodeath/ctdlora",
        "dima806/facial_emotions_image_detection",
        "dima806/mushrooms_image_detection",
        "facebook/SONAR",
        "garage-bAInd/Platypus-30B",
        "gatepoet/Qwen1.5-1.8B-Chat-q4f32_1-MLC",
        "hanungaddi/my-embedding",
        "jarmali/mlprague-workshop",
        "lintonxue00/lora",
        "nihon/SD1.5models",
        "qgallouedec/a2c-CartPole-v1-257778613",
        "qgallouedec/tqc-Humanoid-v3-2048752035",
        "stablediffusionapi/graphic-art",
        "timm/tresnet_m.miil_in1k_448",
        "timm/twins_svt_large.in1k",
        "timm/xcit_large_24_p8_224.fb_dist_in1k",
        "uwg/modelz_base",
        "CyberHarem/tokarev_girlsfrontline",
    }
    previous_repos = previous_repos - exclude_repos
    # Step 2: Sample recent repositories.
    df_recent = sample(df, seed=42, previous_repos=previous_repos, exclude_repos=exclude_repos)
    df_recent.reset_index(drop=True, inplace=True)

    print(f"Selected repositories: {len(df_recent)} recent repos")

    # Step 3: Save the sampled repositories.
    df_recent.to_json(out_recent_models_file, orient="records", indent=2)
    print("Done!")
    print("Recommended next steps:")
    print("\t- Run the get_commit_logs.py to download the commits logs for the selected repositories.")
