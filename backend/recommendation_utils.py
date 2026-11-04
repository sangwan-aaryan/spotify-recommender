import numpy as np
from scipy import sparse


def cosine_similarity_scores(input_vector, matrix):

    if sparse.issparse(matrix):

        matrix_squared_norms = np.asarray(
            matrix.multiply(matrix)
            .sum(axis=1)
        ).ravel()

        input_squared_norm = float(
            input_vector.multiply(input_vector)
            .sum()
        )

        dot_products = matrix @ input_vector.T

        if sparse.issparse(dot_products):
            dot_products = dot_products.toarray()

        dot_products = np.asarray(
            dot_products
        ).ravel()

    else:

        matrix_squared_norms = np.einsum(
            "ij,ij->i",
            matrix,
            matrix
        )

        input_squared_norm = float(
            np.einsum(
                "ij,ij->",
                input_vector,
                input_vector
            )
        )

        dot_products = np.asarray(
            matrix @ input_vector.T
        ).ravel()

    denominators = (
        np.sqrt(matrix_squared_norms)
        * np.sqrt(input_squared_norm)
    )

    scores = np.zeros_like(
        dot_products,
        dtype=float
    )

    np.divide(
        dot_products,
        denominators,
        out=scores,
        where=denominators != 0
    )

    return scores
