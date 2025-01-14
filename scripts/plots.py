from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import ast
import os
from typing import *
import logging
from scipy.signal import savgol_filter

logger = logging.getLogger(__name__)


def find_plateau(y, min_points=30, stability_threshold=0.001):
    """
    Walk backward from the end of 'y' in windows of size 'min_points'.
    Stop if the mean changes by less than 'stability_threshold'
    between consecutive windows. Return the mean of that plateau region.
    """
    try:
        n = len(y)
        i = n - min_points
        plateau_found = False

        while i > min_points:
            current_window = y[i : i + min_points]
            prev_window = y[i - min_points : i]

            current_mean = np.mean(current_window)
            prev_mean = np.mean(prev_window)

            if abs(current_mean - prev_mean) < stability_threshold:
                plateau_found = True
                break
            i -= 1

        if plateau_found:
            # Return mean of from 'i' to the end
            return np.mean(y[i:])
        else:
            # fallback: if no stable plateau found, just use last 'min_points'
            return False
    except Exception as e:
        logger.error(f"Error: ", e)


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

        final_val = find_plateau(y_smooth, min_points=30, stability_threshold=0.005)
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

    # try:
    #     # Ensure both x and y have the same length after dropping NaN
    #     if len(x) != len(y):
    #         min_length = min(len(x), len(y))
    #         x, y = x[:min_length], y[:min_length]

    #     # Calculate total change in y
    #     total_change = y[0] - np.mean(y[-10:])
    #     halftime_y = np.mean(y[-10:]) + total_change / 2  # Y-value at halftime

    #     # Find the index of the y value closest to halftime_y
    #     halftime_index = np.abs(y - halftime_y).argmin()
    #     halftime_x = x[halftime_index]  # Get the corresponding x value
    #     # print(halftime_x/60)
    #     return halftime_x / 60
    # except Exception as e:
    #     logger.error(f"Error: {e}", exc_info=True)


# Cleans the data in a segments. We know its strictly decending curve so we can look at max and min Mean_gray
# and see if a point is in that interval


def clean_data(df, interval_size, votes, time_interval, interval_jump):
    logger.info("Cleaning data from outliers")

    clean_df = pd.DataFrame()

    for i in df["Name"].unique():

        sample_df = df[df["Name"] == i]

        votes_df = pd.DataFrame({"Time": sample_df["Time"].unique(), "Votes": 0})

        int_start = 0
        int_end = interval_size * time_interval

        while int_end <= sample_df["Time"].max():

            datapoint = sample_df[
                (sample_df["Time"] >= int_start) & (sample_df["Time"] <= int_end)
            ]

            for _, row in datapoint.iloc[
                1:-1
            ].iterrows():  # Exclude the first and last two rows
                mean_gray_value = row[
                    "Mean_gray"
                ]  # Get the Mean_gray value for the current row
                start_mean_gray = sample_df.loc[
                    sample_df["Time"] == int_start, "Mean_gray"
                ].iloc[
                    0
                ]  # Get the Mean_gray value at int_start
                end_mean_gray = sample_df.loc[
                    sample_df["Time"] == int_end, "Mean_gray"
                ].iloc[0]

                if mean_gray_value > start_mean_gray or mean_gray_value < end_mean_gray:
                    votes_df.loc[votes_df["Time"] == row["Time"], "Votes"] += 1

            int_start += time_interval * (int(interval_size * (1 / interval_jump)))
            int_end += time_interval * (int(interval_size * (1 / interval_jump)))
            print(int_start)
            if int_end > df["Time"].max() and int_start < df["Time"].max():
                int_end = df["Time"].max()

        filtered_df = votes_df[votes_df["Votes"] > votes]

        # Remove the outlier rows from the sample_df
        cleaned_sample_df = sample_df[~sample_df["Time"].isin(filtered_df["Time"])]

        # Append the cleaned sample_df to the clean_df
        clean_df = pd.concat([clean_df, cleaned_sample_df], ignore_index=True)

        # Sort the aggregated clean_df by 'Time'
    clean_df.sort_values(by="Time", inplace=True)

    return clean_df


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

        return halftimes

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

        for name in names:
            halftimes = boxplot_values(df, name)
            data.append(halftimes)
            lables.append(name)

        plt.figure(figsize=(12, 8))
        plt.boxplot(data, labels=lables, patch_artist=True)
        plt.ylabel("Halftimes")
        plt.xlabel("Samples")
        file_path = os.path.join(output_path, f"boxplot.png")
        plt.savefig(file_path, dpi=300)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
