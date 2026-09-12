from pathlib import Path

import pandas as pd

from .data_cleaning import (
    RAW_DATA_PATH,
    clean_data,
    data_for_content_filtering,
    CLEANED_DATA_PATH
)

from .content_based_filtering import (
    train_transformer,
    save_transformed_data
)

from .collaborative_filtering import (
    HISTORY_DATA_PATH,
    create_interaction_matrix,
    create_collab_filtered_data
)

from .transform_filtered_data import (
    build_hybrid_data
)


# =========================================================
# BUILD EVERYTHING
# =========================================================

def main():

    print("=" * 60)

    print(
        "SPOTIFY RECOMMENDER - BUILDING MODEL DATA"
    )

    print("=" * 60)

    # =====================================================
    # 1. LOAD MUSIC DATA
    # =====================================================

    print(
        "\n[1/5] Loading music dataset..."
    )

    if not RAW_DATA_PATH.exists():

        raise FileNotFoundError(
            f"\nMusic dataset not found:\n"
            f"{RAW_DATA_PATH}\n\n"
            f"Make sure this file exists:\n"
            f"data/Music Info.csv"
        )

    raw_music_data = pd.read_csv(
        RAW_DATA_PATH
    )

    print(
        f"Original dataset shape: "
        f"{raw_music_data.shape}"
    )

    # =====================================================
    # 2. CLEAN DATA
    # =====================================================

    print(
        "\n[2/5] Cleaning music data..."
    )

    cleaned_data = clean_data(
        raw_music_data
    )

    cleaned_data.to_csv(
        CLEANED_DATA_PATH,
        index=False
    )

    print(
        f"Cleaned data saved to:\n"
        f"{CLEANED_DATA_PATH}"
    )

    print(
        f"Cleaned dataset shape: "
        f"{cleaned_data.shape}"
    )

    # =====================================================
    # 3. CONTENT BASED
    # =====================================================

    print(
        "\n[3/5] Building content-based model..."
    )

    content_data = (
        data_for_content_filtering(
            cleaned_data
        )
    )

    transformed_data = (
        train_transformer(
            content_data
        )
    )

    save_transformed_data(
        transformed_data
    )

    # =====================================================
    # 4. COLLABORATIVE
    # =====================================================

    print(
        "\n[4/5] Building collaborative model..."
    )

    if not HISTORY_DATA_PATH.exists():

        raise FileNotFoundError(
            f"\nListening history not found:\n"
            f"{HISTORY_DATA_PATH}\n\n"
            f"Make sure this file exists:\n"
            f"data/User Listening History.csv"
        )

    listening_history = pd.read_csv(
        HISTORY_DATA_PATH
    )

    print(
        f"Listening history shape: "
        f"{listening_history.shape}"
    )

    (
        interaction_matrix,
        track_ids
    ) = create_interaction_matrix(
        cleaned_data,
        listening_history
    )

    create_collab_filtered_data(
        cleaned_data,
        track_ids
    )

    # =====================================================
    # 5. HYBRID
    # =====================================================

    print(
        "\n[5/5] Building hybrid model..."
    )

    build_hybrid_data()

    # =====================================================
    # COMPLETE
    # =====================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "BUILD COMPLETE"
    )

    print(
        "=" * 60
    )

    print(
        "\nGenerated files:"
    )

    data_dir = (
        Path(__file__).resolve().parent.parent
        / "data"
    )

    generated_files = [
        "cleaned_data.csv",
        "transformer.joblib",
        "transformed_data.npz",
        "collab_filtered_data.csv",
        "interaction_matrix.npz",
        "track_ids.npy",
        "transformed_hybrid_data.npz"
    ]

    for filename in generated_files:

        file_path = (
            data_dir / filename
        )

        if file_path.exists():

            print(
                f"  ✓ {filename}"
            )

        else:

            print(
                f"  ✗ {filename} NOT FOUND"
            )

    print(
        "\nAll generated files are inside:"
    )

    print(
        data_dir
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()