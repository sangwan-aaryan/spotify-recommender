from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from category_encoders import CountEncoder

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import (
    MinMaxScaler,
    OneHotEncoder,
    StandardScaler
)

from scipy.sparse import (
    save_npz,
    load_npz
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CLEANED_DATA_PATH = (
    DATA_DIR / "cleaned_data.csv"
)

TRANSFORMER_PATH = (
    DATA_DIR / "transformer.joblib"
)

TRANSFORMED_DATA_PATH = (
    DATA_DIR / "transformed_data.npz"
)


# =========================================================
# FEATURES
# =========================================================

frequency_encode_cols = [
    "year"
]

ohe_cols = [
    "artist",
    "time_signature",
    "key"
]

tfidf_col = "tags"

standard_scale_cols = [
    "duration_ms",
    "loudness",
    "tempo"
]

min_max_scale_cols = [
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence"
]


# =========================================================
# CREATE TRANSFORMER
# =========================================================

def create_transformer():

    transformer = ColumnTransformer(

        transformers=[

            (
                "frequency_encode",

                CountEncoder(
                    normalize=True,
                    return_df=True
                ),

                frequency_encode_cols
            ),

            (
                "ohe",

                OneHotEncoder(
                    handle_unknown="ignore"
                ),

                ohe_cols
            ),

            (
                "tfidf",

                TfidfVectorizer(
                    max_features=85
                ),

                tfidf_col
            ),

            (
                "standard_scale",

                StandardScaler(),

                standard_scale_cols
            ),

            (
                "min_max_scale",

                MinMaxScaler(),

                min_max_scale_cols
            )
        ],

        remainder="passthrough",

        n_jobs=-1
    )

    return transformer


# =========================================================
# TRAIN TRANSFORMER
# =========================================================

def train_transformer(
    data: pd.DataFrame
):

    transformer = create_transformer()

    print(
        "Training content-based transformer..."
    )

    transformed_data = (
        transformer.fit_transform(data)
    )

    joblib.dump(
        transformer,
        TRANSFORMER_PATH
    )

    print(
        f"Transformer saved to:\n"
        f"{TRANSFORMER_PATH}"
    )

    return transformed_data


# =========================================================
# TRANSFORM DATA
# =========================================================

def transform_data(
    data: pd.DataFrame
):

    if not TRANSFORMER_PATH.exists():

        raise FileNotFoundError(
            f"Transformer not found:\n"
            f"{TRANSFORMER_PATH}\n\n"
            f"Run build_models.py first."
        )

    transformer = joblib.load(
        TRANSFORMER_PATH
    )

    transformed_data = (
        transformer.transform(data)
    )

    return transformed_data


# =========================================================
# SAVE TRANSFORMED DATA
# =========================================================

def save_transformed_data(
    transformed_data
):

    save_npz(
        TRANSFORMED_DATA_PATH,
        transformed_data
    )

    print(
        f"Transformed data saved to:\n"
        f"{TRANSFORMED_DATA_PATH}"
    )


# =========================================================
# LOAD TRANSFORMED DATA
# =========================================================

def load_transformed_data():

    if not TRANSFORMED_DATA_PATH.exists():

        raise FileNotFoundError(
            f"Transformed data not found:\n"
            f"{TRANSFORMED_DATA_PATH}"
        )

    return load_npz(
        TRANSFORMED_DATA_PATH
    )


# =========================================================
# CONTENT RECOMMENDATION
# =========================================================

def content_recommendation(
    song_name,
    artist_name,
    songs_data,
    transformed_data,
    k=10
):

    song_name = (
        str(song_name)
        .lower()
        .strip()
    )

    artist_name = (
        str(artist_name)
        .lower()
        .strip()
    )

    songs_data = songs_data.copy()

    # -----------------------------------------------------
    # Find song
    # -----------------------------------------------------

    matching_rows = songs_data[
        (
            songs_data["name"]
            .astype(str)
            .str.lower()
            .str.strip()
            == song_name
        )
        &
        (
            songs_data["artist"]
            .astype(str)
            .str.lower()
            .str.strip()
            == artist_name
        )
    ]

    if matching_rows.empty:

        raise ValueError(
            f"Song '{song_name}' by "
            f"'{artist_name}' was not found."
        )

    # Because the dataframe was reset during cleaning,
    # this index corresponds to transformed_data.
    song_index = matching_rows.index[0]

    # -----------------------------------------------------
    # Input vector
    # -----------------------------------------------------

    input_vector = (
        transformed_data[song_index]
        .reshape(1, -1)
    )

    # -----------------------------------------------------
    # Similarity
    # -----------------------------------------------------

    similarities = cosine_similarity(
        input_vector,
        transformed_data
    ).flatten()

    # -----------------------------------------------------
    # Get recommendations
    # -----------------------------------------------------

    top_indices = np.argsort(
        similarities
    )[::-1][:k + 1]

    recommendations = (
        songs_data.iloc[
            top_indices
        ].copy()
    )

    recommendations["score"] = (
        similarities[top_indices]
    )

    # Remove requested song itself
    recommendations = recommendations[
        ~(
            (
                recommendations["name"]
                .astype(str)
                .str.lower()
                .str.strip()
                == song_name
            )
            &
            (
                recommendations["artist"]
                .astype(str)
                .str.lower()
                .str.strip()
                == artist_name
            )
        )
    ]

    recommendations = (
        recommendations
        .head(k)
        .reset_index(drop=True)
    )

    # -----------------------------------------------------
    # Return useful columns
    # -----------------------------------------------------

    columns = [
        column
        for column in [
            "name",
            "artist",
            "spotify_preview_url",
            "score"
        ]
        if column in recommendations.columns
    ]

    return recommendations[
        columns
    ]