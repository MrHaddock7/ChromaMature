import numpy as np


# Determine a 95% bootstrap confidence interval for the halftime values
# with the assumption that they are the same
def bootstrap_mean(halftimes, n_iterations=10000, alpha=0.05):
    # Collect the mean of each bootstrap sample
    bootstrap_means = []
    for _ in range(n_iterations):
        sample = np.random.choice(halftimes, size=len(halftimes), replace=True)
        bootstrap_means.append(np.mean(sample))
    bootstrap_means = np.array(bootstrap_means)

    # Calculate the lower and upper percentiles
    lower = np.percentile(bootstrap_means, 100 * (alpha / 2))
    upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))

    # Return a tuple: (confidence interval tuple, mean of the original halftimes)
    return ((lower, upper), np.mean(halftimes))
