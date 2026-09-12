from pathlib import Path
import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

# Project root:
# D:\sportyfy\spotify-recommender

BASE_DIR = Path(__file__).resolve().parent.parent

# Use the existing ROOT data folder
DATA_DIR = BASE_DIR / "data"

# Raw dataset
RAW_DATA_PATH = DATA_DIR / "Music Info.csv"

# Generated cleaned dataset
CLEANED_DATA_PATH = DATA_DIR / "cleaned_data.csv"


# =========================================================
# CLEAN DATA
# =========================================================

def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the Spotify music dataset.
    """

    data = data.copy()

    # Remove duplicate tracks
    if "track_id" in data.columns:
        data = data.drop_duplicates(
            subset=["track_id"],
            keep="first"
        )

    # Remove unnecessary columns
    columns_to_drop = []

    for column in ["genre", "spotify_id"]:
        if column in data.columns:
            columns_to_drop.append(column)

    if columns_to_drop:
        data = data.drop(
            columns=columns_to_drop
        )

    # Handle missing tags
    if "tags" in data.columns:
        data["tags"] = data["tags"].fillna(
            "no_tags"
        )
    else:
        data["tags"] = "no_tags"

    # Convert text columns to lowercase
    for column in ["name", "artist", "tags"]:

        if column in data.columns:

            data[column] = (
                data[column]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.strip()
            )

    # Reset index
    data = data.reset_index(
        drop=True
    )

    return data


# =========================================================
# CONTENT FILTERING DATA
# =========================================================

def data_for_content_filtering(
    data: pd.DataFrame
) -> pd.DataFrame:
    """
    Prepare data for content-based filtering.
    """

    data = data.copy()

    columns_to_drop = [
        "track_id",
        "name",
        "spotify_preview_url"
    ]

    # Only drop columns that actually exist
    columns_to_drop = [
        column
        for column in columns_to_drop
        if column in data.columns
    ]

    return data.drop(
        columns=columns_to_drop
    )


# =========================================================
# BUILD CLEAN DATASET
# =========================================================

def build_cleaned_data():

    # Check raw dataset
    if not RAW_DATA_PATH.exists():

        raise FileNotFoundError(
            f"\nDataset not found:\n"
            f"{RAW_DATA_PATH}\n\n"
            f"Make sure your file is named:\n"
            f"Music Info.csv\n"
            f"and is inside the data folder."
        )

    print(
        f"Loading dataset:\n"
        f"{RAW_DATA_PATH}"
    )

    # Read CSV
    data = pd.read_csv(
        RAW_DATA_PATH
    )

    print(
        f"Original dataset shape: "
        f"{data.shape}"
    )

    # Clean
    cleaned_data = clean_data(
        data
    )

    print(
        f"Cleaned dataset shape: "
        f"{cleaned_data.shape}"
    )

    # Save to ROOT data folder
    cleaned_data.to_csv(
        CLEANED_DATA_PATH,
        index=False
    )

    print(
        f"\nCleaned dataset saved to:\n"
        f"{CLEANED_DATA_PATH}"
    )

    return cleaned_data


# =========================================================
# RUN DIRECTLY
# =========================================================

if __name__ == "__main__":
    build_cleaned_data()