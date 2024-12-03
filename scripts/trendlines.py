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
    total_change = y.max() - y[-10:].min()
    halftime_y = y[-10:].min() + total_change / 2  # Y-value at halftime

    # Find the index of the y value closest to halftime_y
    halftime_index = np.abs(y - halftime_y).argmin()
    halftime_x = x[halftime_index]  # Get the corresponding x value
    # print(halftime_x/60)
    return halftime_x / 60


def calculations(csv):
    """
    Process the CSV file and compute halftimes, applying necessary filters and transformations.
    """
    df = pd.read_csv(csv)
    data = []

    # Filter rows based on 'Mean_gray' values
    df = df[(df["Mean_gray"] >= 40) & (df["Mean_gray"] <= 160)]

    # Convert 'gray' from string to list if necessary
    df["gray"] = df["gray"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    # Loop over each unique sample
    for sample in df["Name"].unique():
        sample_df = df[df["Name"] == sample]
        sample_df = sample_df.sort_values(by="Time")
        print(sample_df["Color"].values.tolist()[0])

        # Convert 'Time' and 'Mean_gray' to numeric types, handling errors
        x = (
            pd.to_numeric(sample_df["Time"], errors="coerce").dropna().values
        )  # Convert to numpy array of floats
        y = (
            pd.to_numeric(sample_df["Mean_gray"], errors="coerce").dropna().values
        )  # Convert to numpy array of floats

        halftimes_list = []

        # Check if 'gray' column is empty
        if not sample_df["gray"].iloc[0]:
            print(f"No 'gray' data for sample {sample}. Skipping.")
            continue

        # Determine the number of elements in 'gray' lists
        num_elements = len(sample_df["gray"].iloc[0])

        for i in range(num_elements):
            gray = []
            for j in sample_df["gray"].values.tolist():
                # Ensure that each 'gray' entry is a list and has enough elements
                if isinstance(j, list) and len(j) > i:
                    gray.append(j[i])
                else:
                    gray.append(np.nan)  # Handle missing data
            gray = np.array(gray)

            # Compute halftime, handling NaN values
            if np.isnan(gray).all():
                halftimes_list.append(np.nan)
            else:
                # Remove NaN values from gray and corresponding x
                valid_indices = ~np.isnan(gray) & ~np.isnan(x)
                if np.any(valid_indices):
                    halftimes_list.append(
                        halftime(x[valid_indices], gray[valid_indices])
                    )
                else:
                    halftimes_list.append(np.nan)

        # Apply Savitzky-Golay filter
        try:
            yhat = savgol_filter(y, 52, 1)
        except Exception as e:
            print(f"Error fitting Savitzky-Golay filter: {e}")
            yhat = np.full_like(y, np.nan)  # Assign NaNs or handle as needed

        # Extract the first color from 'Color' column and strip quotes
        color_series = sample_df["Color"]
        if color_series.empty:
            sample_color = "blue"  # Default color if 'Color' column is missing
            print(
                f"No 'Color' data for sample {sample}. Assigning default color 'blue'."
            )
        else:
            # Assuming all colors in the sample are the same
            sample_color_raw = color_series.iloc[0]
            if isinstance(sample_color_raw, str):
                sample_color = sample_color_raw.strip(
                    "'\""
                )  # Remove any surrounding quotes
                print(
                    f"Assigned color '{sample_color}' to sample '{sample}'."
                )  # Debugging
            else:
                sample_color = "blue"  # Default color if not a string
                print(
                    f"Invalid 'Color' format for sample {sample}. Assigning default color 'blue'."
                )

        data.append(
            {
                "sample": sample,
                "x": list(x),
                "y": list(y),
                "yhat": list(yhat),
                "color": sample_color,  # Corrected assignment
                "halftimes": halftimes_list,
            }
        )

    return pd.DataFrame(data)


def scatter_plot(df, output):
    """
    Generate scatter plots for each sample, saving them as SVG files.

    Parameters:
    - df (pd.DataFrame): DataFrame containing plot data.
    - output (str): Directory to save the scatter plots.
    """
    if df is None or df.empty:
        print("DataFrame is empty or None, exiting scatter plot function.")
        return

    # Ensure the output directory exists
    os.makedirs(output, exist_ok=True)

    for _, row in df.iterrows():
        # Convert lists back to numpy arrays for plotting
        x = np.array(row["x"]) / 60  # Convert minutes to hours
        y = np.array(row["y"])
        yhat = np.array(row["yhat"])
        color = row["color"]
        print(color)

        # Validate and strip quotes from color
        if isinstance(color, str):
            clean_color = color.strip("'\"")
        else:
            clean_color = "black"  # Default color if not a string
            print(
                f"Invalid color format for sample {row['sample']}. Assigning default color 'blue'."
            )

        print(
            f"Plotting sample: {row['sample']} with color: {clean_color}"
        )  # Debugging

        try:
            plt.scatter(x, y, marker="o", c=clean_color, label="Data Points")
            if not np.isnan(yhat).all():
                plt.plot(x, yhat, linestyle="--", color="black", label="Trendline")
        except ValueError as ve:
            print(f"Error plotting sample {row['sample']}: {ve}")
            continue  # Skip this plot if there's an error with color

        plt.xlabel("Time [h]")
        plt.ylabel("Grayscale value")
        plt.title(f'Grayscale scatterplot of {row["sample"]}')
        plt.grid(True)

        # Avoid duplicate legends
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys())

        # Replace spaces with underscores for filenames
        sanitized_sample = row["sample"].replace(" ", "_")
        plot_filename = f"{output}/{sanitized_sample}_fixed.svg"

        # Save the plot
        plt.savefig(plot_filename)
        plt.close()

        print(f"Saved scatter plot to {plot_filename}")  # Debugging


def prepare_boxplot_data(df):
    """
    Prepare data for boxplotting by aggregating halftime values for each sample.

    Parameters:
    - df (pd.DataFrame): DataFrame containing 'sample', 'halftimes', and 'color' columns.

    Returns:
    - samples (List[str]): List of sample names.
    - halftimes_data (List[List[float]]): List of halftime values per sample.
    - colors (List[str]): List of colors per sample.
    """
    samples = df["sample"].tolist()
    halftimes_data = df["halftimes"].tolist()
    colors = df["color"].tolist()

    # Ensure that each 'halftimes' entry is a list
    halftimes_data = [ht if isinstance(ht, list) else [] for ht in halftimes_data]

    # Optionally, remove NaN values
    halftimes_data = [
        [ht for ht in sample_ht if not np.isnan(ht) and ht < 48]
        for sample_ht in halftimes_data
    ]

    return samples, halftimes_data, colors


def boxplot_with_points_seaborn(df, output):
    """
    Create a boxplot for each sample with halftime points overlayed using Seaborn.

    Parameters:
    - df (pd.DataFrame): DataFrame containing 'sample', 'halftimes', and 'color' columns.
    - output (str): Directory to save the boxplot image.
    """

    # Prepare data
    samples, halftimes_data, colors = prepare_boxplot_data(df)

    # Create a palette dict mapping samples to their colors
    palette = dict(zip(samples, colors))

    # Remove samples with no halftime data
    samples_filtered = []
    halftimes_filtered = []
    for sample, halftimes in zip(samples, halftimes_data):
        if halftimes:  # Only include samples with at least one halftime value
            samples_filtered.append(sample)
            halftimes_filtered.append(halftimes)

    if not halftimes_filtered:
        print("No halftime data available for boxplot.")
        return

    # Create a long-form DataFrame suitable for Seaborn
    boxplot_df = pd.DataFrame(
        {
            "sample": np.repeat(
                samples_filtered, [len(ht) for ht in halftimes_filtered]
            ),
            "halftime": np.concatenate(halftimes_filtered),
        }
    )

    # Remove NaN halftime values (if any)
    boxplot_df = boxplot_df.dropna(subset=["halftime"])

    # Create the boxplot with Seaborn
    plt.figure(figsize=(12, 8))
    sns.boxplot(
        x="sample", y="halftime", data=boxplot_df, palette=palette, showfliers=False
    )
    sns.stripplot(
        x="sample",
        y="halftime",
        data=boxplot_df,
        color="black",
        size=3,
        jitter=True,
        alpha=0.6,
    )

    # Customize plot
    plt.xlabel("Sample")
    plt.ylabel("Halftime Values [h]")
    plt.title("Halftime Distribution per Sample")
    plt.xticks(rotation=45, ha="right")  # Rotate sample names for better readability
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)

    # Adjust layout to prevent clipping of tick-labels
    plt.tight_layout()

    # Ensure the output directory exists
    os.makedirs(output, exist_ok=True)

    # Save the plot
    plt.savefig(f"{output}/halftime_48.svg")
    plt.savefig(f"{output}/halftime_48.png")
    plt.close()

    print(f"Seaborn boxplot saved to {output}/")


# Execute the calculations function and generate scatter plots
data_df = calculations()
scatter_plot(data_df)

# Generate the boxplot with halftime points
# boxplot_with_points_seaborn(data_df)


# Blir fel vid tidpunkt 865
# Slutar vid tidpunkt 980
