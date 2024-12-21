from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
import ast
import seaborn as sns
import os


def halftime(x, y):
    """
    Calculate the halftime (the x-value where y reaches half of its total change).
    """
    # Ensure both x and y have the same length after dropping NaN
    if len(x) != len(y):
        min_length = min(len(x), len(y))
        x, y = x[:min_length], y[:min_length]

    # Calculate total change in y
    total_change = y[0] - np.mean(y[-10:])
    halftime_y = np.mean(y[-10:]) + total_change / 2  # Y-value at halftime

    # Find the index of the y value closest to halftime_y
    halftime_index = np.abs(y - halftime_y).argmin()
    halftime_x = x[halftime_index]  # Get the corresponding x value
    # print(halftime_x/60)
    return halftime_x / 60


def scatterplot(df, name):
    df = df[df["Name"] == name]
    y = df["Mean_gray"]
    x = df["Time"]

    plt.scatter(x, y, "o", c=df["Color"])
    plt.xlabel("Time")
    plt.ylabel("Grayscale value")

    plt.savefig()
