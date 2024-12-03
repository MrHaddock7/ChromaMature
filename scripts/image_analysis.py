import os
import subprocess
import sys
import cv2
import numpy as np
import csv
from matplotlib import pyplot as plt
import pandas as pd
import re


def extract_and_compute(filename, start_num):
    """
    Extract the last four digits from the filename and convert them to a timestamp value.

    :param filename: The name of the file.
    :return: Extracted timestamp value.
    """
    # Extract the last four digits from the filename using regular expression
    match = re.search(r"(\d{4})\.JPG$", filename)
    if not match:
        raise ValueError("Filename does not contain the required four digits pattern.")

    timestamp_value = int(match.group(1))
    computed_value = (timestamp_value * 5) - (start_num * 5)

    return computed_value


def get_color_intensity(image, coordinates, roi_size=5):
    """
    Get the color intensity and vibrancy at the given coordinates.
    Coordinates should be a list of (x, y) tuples.
    """
    x, y = coordinates
    if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
        x1, y1 = max(0, x - roi_size), max(0, y - roi_size)
        x2, y2 = min(image.shape[1], x + roi_size), min(image.shape[0], y + roi_size)

        roi = image[y1:y2, x1:x2]

        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        mean_gray_intensity = np.mean(gray_roi)

    else:
        mean_gray_intensity = -1

    return mean_gray_intensity


def process_images(folder_path, coordinates, start_num, roi_size=5):
    """
    Process all images in the given folder and calculate color intensity and vibrancy
    at the specified coordinates.
    """
    df = pd.read_csv(coordinates)
    results = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".bmp")):
            image_path = os.path.join(folder_path, filename)
            image = cv2.imread(image_path)
            if image is not None:
                computed_value = extract_and_compute(filename, start_num)
                for sample in df["name"].unique().tolist():
                    grays = []
                    sample_coords = df[df["name"] == sample][["x", "y"]]
                    for _, row in sample_coords.iterrows():
                        coord = (row["x"], row["y"])
                        # Compute the color intensity using your function
                        gray = get_color_intensity(image, coord, roi_size)
                        grays.append(gray)

                    results.append(
                        (
                            computed_value,
                            sample,
                            df[df["name"] == sample]["color"].tolist()[0],
                            np.mean(grays),
                            grays,
                        )
                    )
    return results


def csv_writer(results, path=""):
    headers = ["Time", "Name", "Color", "Mean_gray", "gray"]
    csv_path = path

    with open(csv_path, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if csvfile.tell() == 0:
            writer.writerow(headers)
        for result in results:
            writer.writerow(result)

    df = pd.read_csv(csv_path)
    df_sorted = df.sort_values(by="Time")
    df_sorted.to_csv(csv_path, index=False)


if __name__ == "__main__":
    # Process images
    results = process_images()

    # Write results to CSV
    csv_writer(results, path="results.csv")
