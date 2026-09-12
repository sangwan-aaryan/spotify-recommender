from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field

from scipy.sparse import load_npz

from .content_based_filtering import content_recommendation
from .collaborative_filtering import collaborative_recommendation
from .hybrid_recommendations import HybridRecommenderSystem


# =========================================================
# PATHS
# =========================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATA_DIR = BASE_DIR / "data"


CLEANED_DATA_PATH = (
    DATA_DIR / "cleaned_data.csv"
)

COLLAB_DATA_PATH = (
    DATA_DIR / "collab_filtered_data.csv"
)

TRANSFORMED_DATA_PATH = (
    DATA_DIR / "transformed_data.npz"
)

HYBRID_TRANSFORMED_DATA_PATH = (
    DATA_DIR / "transformed_hybrid_data.npz"
)

TRACK_IDS_PATH = (
    DATA_DIR / "track_ids.npy"
)

INTERACTION_MATRIX_PATH = (
    DATA_DIR / "interaction_matrix.npz"
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Spotify Recommendation API",
    description=(
        "Spotify-like song recommendation "
        "API using Content-Based, "
        "Collaborative and Hybrid Filtering."
    ),
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",

        "http://localhost:5173",
        "http://127.0.0.1:5173",

        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODEL
# =========================================================

class RecommendationRequest(BaseModel):

    song_name: str = Field(
        ...,
        min_length=1
    )

    artist_name: str = Field(
        ...,
        min_length=1
    )

    k: int = Field(
        default=10,
        ge=5,
        le=20
    )

    filtering_type: Literal[
        "Content-Based Filtering",
        "Collaborative Filtering",
        "Hybrid Recommender System"
    ] = Field(
        default="Hybrid Recommender System"
    )

    diversity: int = Field(
        default=5,
        ge=1,
        le=10
    )


# =========================================================
# GLOBAL DATA
# =========================================================

songs_data = None
filtered_data = None
transformed_data = None
transformed_hybrid_data = None
track_ids = None
interaction_matrix = None


# =========================================================
# LOAD DATA
# =========================================================

def load_recommendation_data():

    global songs_data
    global filtered_data
    global transformed_data
    global transformed_hybrid_data
    global track_ids
    global interaction_matrix

    required_files = [
        CLEANED_DATA_PATH,
        COLLAB_DATA_PATH,
        TRANSFORMED_DATA_PATH,
        HYBRID_TRANSFORMED_DATA_PATH,
        TRACK_IDS_PATH,
        INTERACTION_MATRIX_PATH
    ]

    missing_files = [
        str(file)
        for file in required_files
        if not file.exists()
    ]

    if missing_files:

        raise FileNotFoundError(
            "Required recommendation files are missing:\n\n"
            + "\n".join(missing_files)
            + "\n\nRun:\n"
            "python -m backend.build_models"
        )

    print("\nLoading recommendation data...")

    # -----------------------------------------------------
    # CSV
    # -----------------------------------------------------

    songs_data = pd.read_csv(
        CLEANED_DATA_PATH
    )

    filtered_data = pd.read_csv(
        COLLAB_DATA_PATH
    )

    # -----------------------------------------------------
    # Sparse matrices
    # -----------------------------------------------------

    transformed_data = load_npz(
        TRANSFORMED_DATA_PATH
    )

    transformed_hybrid_data = load_npz(
        HYBRID_TRANSFORMED_DATA_PATH
    )

    interaction_matrix = load_npz(
        INTERACTION_MATRIX_PATH
    )

    # -----------------------------------------------------
    # Track IDs
    # -----------------------------------------------------

    track_ids = np.load(
        TRACK_IDS_PATH,
        allow_pickle=True
    )

    print(
        f"Songs loaded: "
        f"{len(songs_data)}"
    )

    print(
        f"Collaborative songs loaded: "
        f"{len(filtered_data)}"
    )

    print(
        f"Content matrix shape: "
        f"{transformed_data.shape}"
    )

    print(
        f"Hybrid matrix shape: "
        f"{transformed_hybrid_data.shape}"
    )

    print(
        f"Interaction matrix shape: "
        f"{interaction_matrix.shape}"
    )

    print(
        "Recommendation data loaded successfully."
    )


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup_event():

    try:

        load_recommendation_data()

    except Exception as error:

        print(
            "\nWARNING:"
        )

        print(
            "Recommendation data could not be loaded."
        )

        print(
            f"\nReason:\n{error}"
        )

        print(
            "\nRun:"
        )

        print(
            "python -m backend.build_models"
        )


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "models_loaded": songs_data is not None
    }


# =========================================================
# RECOMMENDATION API
# =========================================================

@app.post("/recommend")
def recommend(
    request: RecommendationRequest
):

    # -----------------------------------------------------
    # Check models
    # -----------------------------------------------------

    if songs_data is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "Recommendation data is not loaded. "
                "Run: python -m backend.build_models"
            )
        )

    song_name = (
        request.song_name
        .strip()
        .lower()
    )

    artist_name = (
        request.artist_name
        .strip()
        .lower()
    )

    # =====================================================
    # CONTENT BASED
    # =====================================================

    if request.filtering_type == (
        "Content-Based Filtering"
    ):

        try:

            recommendations = (
                content_recommendation(
                    song_name=song_name,
                    artist_name=artist_name,
                    songs_data=songs_data,
                    transformed_data=transformed_data,
                    k=request.k
                )
            )

        except ValueError as error:

            raise HTTPException(
                status_code=404,
                detail=str(error)
            )

        return {
            "success": True,
            "song_name": request.song_name,
            "artist_name": request.artist_name,
            "filtering_type": request.filtering_type,
            "diversity": request.diversity,
            "count": len(recommendations),
            "recommendations": (
                recommendations
                .fillna("")
                .to_dict(
                    orient="records"
                )
            )
        }

    # =====================================================
    # COLLABORATIVE
    # =====================================================

    if request.filtering_type == (
        "Collaborative Filtering"
    ):

        matching_song = filtered_data[
            (
                filtered_data["name"]
                .astype(str)
                .str.lower()
                .str.strip()
                == song_name
            )
            &
            (
                filtered_data["artist"]
                .astype(str)
                .str.lower()
                .str.strip()
                == artist_name
            )
        ]

        if matching_song.empty:

            raise HTTPException(
                status_code=404,
                detail=(
                    "This song is not available "
                    "in the collaborative dataset."
                )
            )

        try:

            recommendations = (
                collaborative_recommendation(
                    song_name=song_name,
                    artist_name=artist_name,
                    track_ids=track_ids,
                    songs_data=filtered_data,
                    interaction_matrix=interaction_matrix,
                    k=request.k
                )
            )

        except ValueError as error:

            raise HTTPException(
                status_code=404,
                detail=str(error)
            )

        return {
            "success": True,
            "song_name": request.song_name,
            "artist_name": request.artist_name,
            "filtering_type": request.filtering_type,
            "diversity": request.diversity,
            "count": len(recommendations),
            "recommendations": (
                recommendations
                .fillna("")
                .to_dict(
                    orient="records"
                )
            )
        }

    # =====================================================
    # HYBRID
    # =====================================================

    if request.filtering_type == (
        "Hybrid Recommender System"
    ):

        matching_song = filtered_data[
            (
                filtered_data["name"]
                .astype(str)
                .str.lower()
                .str.strip()
                == song_name
            )
            &
            (
                filtered_data["artist"]
                .astype(str)
                .str.lower()
                .str.strip()
                == artist_name
            )
        ]

        # -------------------------------------------------
        # Hybrid fallback
        # -------------------------------------------------

        if matching_song.empty:

            try:

                recommendations = (
                    content_recommendation(
                        song_name=song_name,
                        artist_name=artist_name,
                        songs_data=songs_data,
                        transformed_data=transformed_data,
                        k=request.k
                    )
                )

            except ValueError as error:

                raise HTTPException(
                    status_code=404,
                    detail=str(error)
                )

            return {
                "success": True,
                "song_name": request.song_name,
                "artist_name": request.artist_name,
                "filtering_type":
                    "Hybrid fallback (Content-Based)",
                "diversity": request.diversity,
                "count": len(recommendations),
                "recommendations": (
                    recommendations
                    .fillna("")
                    .to_dict(
                        orient="records"
                    )
                )
            }

        # -------------------------------------------------
        # Diversity
        # -------------------------------------------------

        content_based_weight = (
            1 -
            (
                request.diversity / 10
            )
        )

        recommender = (
            HybridRecommenderSystem(
                number_of_recommendations=
                    request.k,
                weight_content_based=
                    content_based_weight
            )
        )

        try:

            recommendations = (
                recommender
                .give_recommendations(
                    song_name=song_name,
                    artist_name=artist_name,
                    songs_data=filtered_data,
                    transformed_matrix=
                        transformed_hybrid_data,
                    track_ids=track_ids,
                    interaction_matrix=
                        interaction_matrix
                )
            )

        except ValueError as error:

            raise HTTPException(
                status_code=404,
                detail=str(error)
            )

        return {
            "success": True,
            "song_name": request.song_name,
            "artist_name": request.artist_name,
            "filtering_type": request.filtering_type,
            "diversity": request.diversity,
            "content_weight": round(
                content_based_weight,
                2
            ),
            "collaborative_weight": round(
                1 - content_based_weight,
                2
            ),
            "count": len(recommendations),
            "recommendations": (
                recommendations
                .fillna("")
                .to_dict(
                    orient="records"
                )
            )
        }

    # =====================================================
    # INVALID FILTER
    # =====================================================

    raise HTTPException(
        status_code=400,
        detail="Invalid filtering type."
    )


# =========================================================
# FRONTEND
# =========================================================

app.mount(
    "/",
    StaticFiles(
        directory="frontend",
        html=True
    ),
    name="frontend"
)