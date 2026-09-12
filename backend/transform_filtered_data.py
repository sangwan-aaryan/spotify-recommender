from pathlib import Path

import pandas as pd

from scipy.sparse import save_npz

from .data_cleaning import (
    data_for_content_filtering
)

from .content_based_filtering import (
    transform_data
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

COLLAB_DATA_PATH = (
    DATA_DIR / "collab_filtered_data.csv"
)

HYBRID_DATA_PATH = (
    DATA_DIR / "transformed_hybrid_data.npz"
)


# =========================================================
# BUILD HYBRID DATA
# =========================================================

def build_hybrid_data():

    if not COLLAB_DATA_PATH.exists():

        raise FileNotFoundError(
            f"Collaborative data not found:\n"
            f"{COLLAB_DATA_PATH}\n\n"
            f"Run build_models.py first."
        )

    print(
        "Loading collaborative filtered data..."
    )

    data = pd.read_csv(
        COLLAB_DATA_PATH
    )

    print(
        f"Collaborative data shape: "
        f"{data.shape}"
    )

    # -----------------------------------------------------
    # Prepare content features
    # -----------------------------------------------------

    content_data = (
        data_for_content_filtering(
            data
        )
    )

    print(
        f"Content feature data shape: "
        f"{content_data.shape}"
    )

    # -----------------------------------------------------
    # Transform
    # -----------------------------------------------------

    print(
        "Transforming hybrid data..."
    )

    transformed_data = transform_data(
        content_data
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    save_npz(
        HYBRID_DATA_PATH,
        transformed_data
    )

    print(
        f"Hybrid transformed data saved to:\n"
        f"{HYBRID_DATA_PATH}"
    )


if __name__ == "__main__":
    build_hybrid_data()