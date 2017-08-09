def ldist(a, b):
    """Compute levenshtein distance using
    Wagner-Fischer algorithm

    https://en.wikipedia.org/wiki/Levenshtein_distance
    https://en.wikipedia.org/wiki/Levenshtein_distance#Iterative_with_full_matrix
    """
    matrix = [[0 for _ in range(len(b)+1)] for _ in range(len(a)+1)]
    for i in range(1, len(a)+1):
        matrix[i][0] = i
    for j in range(1, len(b)+1):
        matrix[0][j] = j
    for j in range(1, len(b)+1):
        for i in range(1, len(a)+1):
            if a[i-1] == b[j-1]:
                cost = 0
            else:
                cost = 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,
                matrix[i][j-1] + 1,
                matrix[i-1][j-1] + cost
            )
    return matrix[len(a)][len(b)]
    
