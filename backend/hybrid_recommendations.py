import numpy as np
import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity


class HybridRecommenderSystem:

    def __init__(
        self,
        number_of_recommendations=10,
        weight_content_based=0.5
    ):

        self.number_of_recommendations = (
            number_of_recommendations
        )

        self.weight_content_based = (
            weight_content_based
        )

        self.weight_collaborative = (
            1 - weight_content_based
        )

    # =====================================================
    # NORMALIZE SCORES
    # =====================================================

    @staticmethod
    def normalize_scores(scores):

        scores = np.asarray(
            scores,
            dtype=float
        )

        minimum = scores.min()
        maximum = scores.max()

        if maximum == minimum:

            return np.zeros_like(
                scores
            )

        return (
            (scores - minimum)
            /
            (maximum - minimum)
        )

    # =====================================================
    # HYBRID RECOMMENDATIONS
    # =====================================================

    def give_recommendations(
        self,
        song_name,
        artist_name,
        songs_data,
        transformed_matrix,
        track_ids,
        interaction_matrix
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

        # -------------------------------------------------
        # Find song in hybrid dataset
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Content similarity
        # -------------------------------------------------

        song_dataframe_index = (
            matching_rows.index[0]
        )

        content_input = (
            transformed_matrix[
                song_dataframe_index
            ].reshape(1, -1)
        )

        content_scores = cosine_similarity(
            content_input,
            transformed_matrix
        ).flatten()

        # -------------------------------------------------
        # Find track ID
        # -------------------------------------------------

        track_id = str(
            matching_rows.iloc[0]["track_id"]
        )

        track_ids_string = np.array(
            [
                str(value)
                for value in track_ids
            ]
        )

        collaborative_indices = np.where(
            track_ids_string == track_id
        )[0]

        if len(collaborative_indices) == 0:

            raise ValueError(
                "Song is not available in "
                "collaborative data."
            )

        collaborative_index = (
            collaborative_indices[0]
        )

        # -------------------------------------------------
        # Collaborative similarity
        # -------------------------------------------------

        collaborative_input = (
            interaction_matrix[
                collaborative_index
            ]
        )

        collaborative_scores = (
            cosine_similarity(
                collaborative_input,
                interaction_matrix
            ).flatten()
        )

        # -------------------------------------------------
        # Normalize
        # -------------------------------------------------

        content_scores = (
            self.normalize_scores(
                content_scores
            )
        )

        collaborative_scores = (
            self.normalize_scores(
                collaborative_scores
            )
        )

        # -------------------------------------------------
        # Create collaborative score map
        # -------------------------------------------------

        collaborative_score_map = {

            track_ids_string[index]:
            float(collaborative_scores[index])

            for index in range(
                len(track_ids_string)
            )
            if index < len(
                collaborative_scores
            )
        }

        # -------------------------------------------------
        # Add collaborative scores to songs
        # -------------------------------------------------

        songs_data["_track_id"] = (
            songs_data["track_id"]
            .astype(str)
        )

        songs_data["_content_score"] = (
            content_scores
        )

        songs_data["_collaborative_score"] = (
            songs_data["_track_id"]
            .map(
                collaborative_score_map
            )
            .fillna(0)
        )

        # -------------------------------------------------
        # Weighted hybrid score
        # -------------------------------------------------

        songs_data["score"] = (

            self.weight_content_based
            *
            songs_data["_content_score"]

            +

            self.weight_collaborative
            *
            songs_data["_collaborative_score"]
        )

        # -------------------------------------------------
        # Remove input song
        # -------------------------------------------------

        recommendations = songs_data[
            ~(
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
            )
        ]

        # -------------------------------------------------
        # Sort by hybrid score
        # -------------------------------------------------

        recommendations = (
            recommendations
            .sort_values(
                "score",
                ascending=False
            )
            .head(
                self.number_of_recommendations
            )
            .copy()
        )

        # -------------------------------------------------
        # Return useful columns
        # -------------------------------------------------

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

        return (
            recommendations[
                columns
            ]
            .reset_index(drop=True)
        )