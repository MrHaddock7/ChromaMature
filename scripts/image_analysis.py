import os
import subprocess
import sys
import cv2
import numpy as np
import csv
from matplotlib import pyplot as plt
import pandas as pd
import 


def pictures(folder_path):
    # Adjust the file extensions if needed
    valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tif")
    all_files = os.listdir(folder_path)

    # Filter image files only
    image_files = [f for f in all_files if f.lower().endswith(valid_extensions)]

    # Sort them if needed (though we assume they are already sorted)
    image_files.sort()

    return enumerate(image_files)


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


def process_images(folder_path, coordinates, time_interval=5, roi_size=5):
    """
    Process all images in the given folder and calculate color intensity and vibrancy
    at the specified coordinates.
    """
    if type(coordinates) == str:
        df = pd.read_csv(coordinates)
    else:
        df = coordinates
    results = []

    filenames = pictures(folder_path)
    time = -time_interval
    filecount = 0
    for filename in filenames:
        filecount += 1
        print(filecount, "/", len(filenames))
        image_path = os.path.join(folder_path, filename)
        image = cv2.imread(image_path)

        if image is not None:
            time += time_interval

            for sample in df["name"].unique().tolist():
                grays = []
                sample_coords = df[df["name"] == sample][["x", "y"]]
                for _, row in sample_coords.iterrows():
                    coord = (row["x"], row["y"])
                    gray = get_color_intensity(image, coord, roi_size)
                    grays.append(gray)

                results.append(
                    (
                        time,
                        sample,
                        df[df["name"] == sample]["color"].tolist()[0],
                        np.mean(grays),
                        grays,
                    )
                )
    return results


def process_images_parallel(folder_path, coordinates, time_interval=5, roi_size=5):
    """
    Process all images in the given folder and calculate color intensity and vibrancy
    at the specified coordinates.
    """
    if type(coordinates) == str:
        df = pd.read_csv(coordinates)
    else:
        df = coordinates
    results = []

    filenames = pictures(folder_path)
    


    for filename in filenames:
        image_path = os.path.join(folder_path, filename)
        image = cv2.imread(image_path)

        if image is not None:
            time += time_interval

            for sample in df["name"].unique().tolist():
                grays = []
                sample_coords = df[df["name"] == sample][["x", "y"]]
                for _, row in sample_coords.iterrows():
                    coord = (row["x"], row["y"])
                    gray = get_color_intensity(image, coord, roi_size)
                    grays.append(gray)

                results.append(
                    (
                        time,
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
    return df_sorted


def run_processing(output_path, picture_folder, coords, time_intervals=5, roi_size=5):
    results = process_images(picture_folder, coords, time_intervals, roi_size)
    return csv_writer(results, output_path)


run_processing(
    "",
    "/Users/william/Library/CloudStorage/OneDrive-Uppsalauniversitet/Igem/Images/Code/Pictures/Thanos_run",
    "data.csv",
)
# if __name__ == "__main__":
#     # Process images
#     results = process_images()

#     # Write results to CSV
#     csv_writer(results, path="results.csv")
