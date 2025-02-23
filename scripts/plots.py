from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import ast
import os
from typing import *
import logging
from scipy.signal import savgol_filter
from scripts.stat_test import bootstrap_mean
import ruptures as rpt

logger = logging.getLogger(__name__)

# Finds the point where the maturation slows to the point where we assume that its done


def find_plateau(y):
    try:
        y_2d = y.reshape(-1, 1)
        algo = rpt.Binseg(model="linear").fit(y_2d)

        result = algo.predict(n_bkps=2)

        break_index = result[0]

        return y[break_index]

    except Exception as e:
        logger.error("Error: ", e)


def halftime(x, y):
    """
    Calculate the halftime (the x-value where y reaches half of its total change).
    """
    try:
        # Ensure both x and y have the same length after dropping NaN
        if len(x) != len(y):
            min_length = min(len(x), len(y))
            x, y = x[:min_length], y[:min_length]

        y_smooth = savgol_filter(y, window_length=11, polyorder=2)

        final_val = find_plateau(y_smooth)
        if final_val is not False:

            total_change = y[0] - final_val
            halftime_y = final_val + (total_change / 2.0)
            halftime_index = np.abs(y - halftime_y).argmin()
            halftime_x = x[halftime_index]

            # Convert to hours
            return halftime_x / 60

        else:
            return False

    except Exception as e:
        logger.error(f"Error: ", e)


def scatterplot_range(df):
    logger.info("Starting scatterplot_range")
    names = df["Name"].unique()

    max_range = -1

    for i in names:

        df_name = df[df["Name"] == i]
        range = df_name["Mean_gray"].max() - df_name["Mean_gray"].min()

        if range > max_range:
            max_range = range

    return max_range


def scatterplot(
    df,
    name,
    figsize: Optional[Tuple[int, int]] = None,
    yrange: Optional[Union[Tuple[int, int], int]] = None,
    output_path: str = None,
) -> None:
    logger.info(f"Creating scatterplot for {name}...")

    try:
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
            if isinstance(yrange, tuple):
                plt.ylim(yrange)
            else:
                difference = yrange - (y.max() - y.min())

                plt.ylim(ymin=y.min() - difference / 2, ymax=y.max() + difference / 2)

        file_path = os.path.join(output_path, f"scatterplot_{name}.png")
        plt.savefig(file_path, dpi=300)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


def boxplot_values(df, name) -> list:
    logger.info(f"Calculating boxplot values for {name}...")

    try:
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

            h_time = halftime(x, y)
            if h_time == False:
                continue
            else:
                halftimes.append(h_time)

        conf_interval = bootstrap_mean(halftimes)
        return halftimes, conf_interval

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


def boxplot(df, output_path: str) -> None:
    logger.info("Generating boxplot.")

    try:
        if type(df) == str:
            df = pd.read_csv(df)

        names = df["Name"].unique()

        data = []
        lables = []
        conf_intervals = []

        for name in names:
            halftimes, conf_interval = boxplot_values(df, name)
            data.append(halftimes)
            lables.append(name)
            conf_intervals.append(conf_interval)

        plt.figure(figsize=(12, 8))
        plt.boxplot(data, labels=lables, patch_artist=True)

        plt.xticks(rotation=45)
        plt.ylabel("Halftimes")
        plt.xlabel("Samples")
        file_path = os.path.join(output_path, f"boxplot.png")
        plt.savefig(file_path, dpi=300)

        return lables, conf_intervals

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
