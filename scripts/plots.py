from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import ast
import seaborn as sns
import os
from typing import *


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


def scatterplot(
    df,
    name,
    figsize: Optional[Tuple[int, int]] = None,
    yrange: Optional[Tuple[int, int]] = None,
    output_path: str = None,
) -> None:

    if type(df) == str:
        df = pd.read_csv(df)

    df = df[df["Name"] == name]
    y = df["Mean_gray"]
    x = df["Time"] / 60

    if figsize:
        plt.figure(figsize=figsize)
    else:
        plt.figure()

    plt.scatter(x, y, c=df["Color"])
    plt.xlabel("Time [h]")
    plt.ylabel("Grayscale value")
    plt.title(f"Mean grayscale values for sample {name}")

    if yrange:
        plt.ylim(yrange)

    file_path = os.path.join(output_path, f"scatterplot_{name}.png")
    plt.savefig(file_path, dpi=300)


def boxplot_values(df, name) -> list:

    if type(df) == str:
        df = pd.read_csv(df)

    df = df[df["Name"] == name]

    halftimes = []

    for i in range(len(ast.literal_eval(df["Gray"].tolist()[0]))):
        x = []
        y = []
        for _, row in df.iterrows():
            x.append(row["Time"])
            y.append(ast.literal_eval(row["Gray"])[i])

        halftimes.append(halftime(x, y))

    return halftimes


def boxplot(df) -> None:

    if type(df) == str:
        df = pd.read_csv(df)

    names = df["Name"].unique()

    data = []
    lables = []

    for name in names:
        halftimes = boxplot_values(df, name)
        data.append(halftimes)
        lables.append(name)

    print(data)
    print(lables)

    plt.boxplot(data, labels=lables, patch_artist=True)
    plt.ylabel("Halftimes")
    plt.xlabel("Samples")
    plt.show()


boxplot("/Users/william/Documents/Github/ChromaMature/tests/data_output.csv")
