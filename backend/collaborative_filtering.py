from pathlib import Path

import numpy as np
import pandas as pd

from scipy.sparse import (
    csr_matrix,
    save_npz,
    load_npz
)

from sklearn.metrics.pairwise import cosine_similarity


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

MUSIC_DATA_PATH = (
    DATA_DIR / "cleaned_data.csv"
)

HISTORY_DATA_PATH = (
    DATA_DIR / "User Listening History.csv"
)

TRACK_IDS_PATH = (
    DATA_DIR / "track_ids.npy"
)

COLLAB_DATA_PATH = (
    DATA_DIR / "collab_filtered_data.csv"
)

INTERACTION_MATRIX_PATH = (
    DATA_DIR / "interaction_matrix.npz"
)


# =========================================================
# CREATE INTERACTION MATRIX
# =========================================================

def create_interaction_matrix(
    music_data: pd.DataFrame,
    listening_history: pd.DataFrame
):

    history = listening_history.copy()

    # -----------------------------------------------------
    # Check columns
    # -----------------------------------------------------

    required_columns = [
        "user_id",
        "track_id",
        "playcount"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in history.columns
    ]

    if missing_columns:

        raise ValueError(
            "Listening history is missing columns: "
            + ", ".join(missing_columns)
        )

    # -----------------------------------------------------
    # Clean values
    # -----------------------------------------------------

    history["playcount"] = pd.to_numeric(
        history["playcount"],
        errors="coerce"
    ).fillna(0)

    history["user_id"] = (
        history["user_id"]
        .astype(str)
    )

    history["track_id"] = (
        history["track_id"]
        .astype(str)
    )

    # -----------------------------------------------------
    # Create categorical mappings
    # -----------------------------------------------------

    track_categories = pd.Categorical(
        history["track_id"]
    )

    user_categories = pd.Categorical(
        history["user_id"]
    )

    track_codes = (
        track_categories.codes
    )

    user_codes = (
        user_categories.codes
    )

    track_ids = (
        track_categories
        .categories
        .astype(str)
    )

    # -----------------------------------------------------
    # Matrix dimensions
    # -----------------------------------------------------

    number_of_tracks = (
        len(track_categories.categories)
    )

    number_of_users = (
        len(user_categories.categories)
    )

    # -----------------------------------------------------
    # Create sparse matrix
    # -----------------------------------------------------

    interaction_matrix = csr_matrix(

        (
            history["playcount"].values,

            (
                track_codes,
                user_codes
            )
        ),

        shape=(
            number_of_tracks,
            number_of_users
        )
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    np.save(
        TRACK_IDS_PATH,
        np.array(track_ids)
    )

    save_npz(
        INTERACTION_MATRIX_PATH,
        interaction_matrix
    )

    print(
        f"Interaction matrix shape: "
        f"{interaction_matrix.shape}"
    )

    print(
        f"Track IDs saved to:\n"
        f"{TRACK_IDS_PATH}"
    )

    print(
        f"Interaction matrix saved to:\n"
        f"{INTERACTION_MATRIX_PATH}"
    )

    return (
        interaction_matrix,
        track_ids
    )


# =========================================================
# CREATE COLLABORATIVE DATASET
# =========================================================

def create_collab_filtered_data(
    music_data: pd.DataFrame,
    track_ids
):

    track_ids = set(
        str(track_id)
        for track_id in track_ids
    )

    filtered_data = music_data[
        music_data["track_id"]
        .astype(str)
        .isin(track_ids)
    ].copy()

    filtered_data = (
        filtered_data
        .reset_index(drop=True)
    )

    filtered_data.to_csv(
        COLLAB_DATA_PATH,
        index=False
    )

    print(
        f"Collaborative dataset saved to:\n"
        f"{COLLAB_DATA_PATH}"
    )

    print(
        f"Collaborative dataset shape: "
        f"{filtered_data.shape}"
    )

    return filtered_data


# =========================================================
# LOAD INTERACTION MATRIX
# =========================================================

def load_interaction_matrix():

    return load_npz(
        INTERACTION_MATRIX_PATH
    )


# =========================================================
# LOAD TRACK IDS
# =========================================================

def load_track_ids():

    return np.load(
        TRACK_IDS_PATH,
        allow_pickle=True
    )


# =========================================================
# COLLABORATIVE RECOMMENDATION
# =========================================================

def collaborative_recommendation(
    song_name,
    artist_name,
    track_ids,
    songs_data,
    interaction_matrix,
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
    # Find requested song
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
            f"'{artist_name}' was not found "
            f"in collaborative data."
        )

    track_id = str(
        matching_rows.iloc[0]["track_id"]
    )

    # -----------------------------------------------------
    # Convert track IDs to strings
    # -----------------------------------------------------

    track_ids_string = np.array(
        [
            str(track_id)
            for track_id in track_ids
        ]
    )

    # -----------------------------------------------------
    # Find matrix row
    # -----------------------------------------------------

    matching_indices = np.where(
        track_ids_string == track_id
    )[0]

    if len(matching_indices) == 0:

        raise ValueError(
            "The requested song is not available "
            "in the interaction matrix."
        )

    track_index = (
        matching_indices[0]
    )

    # -----------------------------------------------------
    # Similarity
    # -----------------------------------------------------

    input_vector = (
        interaction_matrix[
            track_index
        ]
    )

    similarities = cosine_similarity(
        input_vector,
        interaction_matrix
    ).flatten()

    # -----------------------------------------------------
    # Top songs
    # -----------------------------------------------------

    top_indices = np.argsort(
        similarities
    )[::-1][:k + 1]

    recommended_track_ids = [
        track_ids_string[index]
        for index in top_indices
    ]

    # -----------------------------------------------------
    # Filter songs
    # -----------------------------------------------------

    recommendations = songs_data[
        songs_data["track_id"]
        .astype(str)
        .isin(recommended_track_ids)
    ].copy()

    # -----------------------------------------------------
    # Attach score
    # -----------------------------------------------------

    score_map = {
        track_ids_string[index]:
        float(similarities[index])

        for index in top_indices
    }

    recommendations["score"] = (
        recommendations["track_id"]
        .astype(str)
        .map(score_map)
    )

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    recommendations = (
        recommendations
        .sort_values(
            "score",
            ascending=False
        )
    )

    # -----------------------------------------------------
    # Remove requested song
    # -----------------------------------------------------

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
    # Return
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