import os
import cv2
import numpy as np
import csv
import pandas as pd
from concurrent import futures
import logging

logger = logging.getLogger(__name__)


def pictures(folder_path):
    logger.info(f"Retrieving pictures from {folder_path}.")
    try:
        # Adjust the file extensions if needed
        valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tif")
        all_files = os.listdir(folder_path)

        # Filter image files only
        image_files = [f for f in all_files if f.lower().endswith(valid_extensions)]

        # Sort them if needed (though we assume they are already sorted)
        image_files.sort()

        return enumerate(image_files)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


def get_color_intensity(image, coordinates, roi_size=5):
    """
    Get the color intensity and vibrancy at the given coordinates.
    Coordinates should be a list of (x, y) tuples.
    """

    try:
        x, y = coordinates
        if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
            x1, y1 = max(0, x - roi_size), max(0, y - roi_size)
            x2, y2 = min(image.shape[1], x + roi_size), min(
                image.shape[0], y + roi_size
            )

            roi = image[y1:y2, x1:x2]

            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            mean_gray_intensity = float(np.mean(gray_roi))

        else:
            mean_gray_intensity = -1

        return mean_gray_intensity
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


def process_images(folder_path, coordinates, time_interval=5, roi_size=5):
    """
    Process all images in the given folder and calculate color intensity and vibrancy
    at the specified coordinates.
    """
    logger.info(
        f"Processing images in sequential mode with time_interval={time_interval} and roi_size={roi_size}."
    )
    try:
        if type(coordinates) == str:
            df = pd.read_csv(coordinates)
        else:
            df = coordinates
        results = []

        filenames = pictures(folder_path)
        time = -time_interval
        for filename in filenames:
            image_path = os.path.join(folder_path, filename[1])
            image = cv2.imread(image_path)

            if image is not None:
                time += time_interval

                for sample in df["name"].unique().tolist():
                    grays = []
                    sample_coords = df[df["name"] == sample][["y", "x"]]
                    for _, row in sample_coords.iterrows():
                        coord = (row["y"], row["x"])
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
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


def process_images_parallel(folder_path, coordinates, time_interval=5, roi_size=5):
    logger.info(
        f"Processing images in parallel mode with time_interval={time_interval} and roi_size={roi_size}."
    )
    try:
        if isinstance(coordinates, str):
            df = pd.read_csv(coordinates)
        else:
            df = coordinates

        filenames = pictures(folder_path)

        def analysis(filename):
            # Create a local list to store results for this image
            local_results = []

            image_path = os.path.join(folder_path, filename[1])
            image = cv2.imread(image_path)
            time = filename[0] * time_interval

            for sample in df["name"].unique():
                sample_coords = df[df["name"] == sample][["y", "x"]]
                grays = []
                for _, row in sample_coords.iterrows():
                    coord = (row["y"], row["x"])
                    gray = get_color_intensity(image, coord, roi_size)
                    grays.append(gray)

                color = df[df["name"] == sample]["color"].iloc[0]

                if np.mean(grays) == -1:
                    continue
                else:
                    local_results.append((time, sample, color, np.mean(grays), grays))

            return local_results

        # Execute analysis in parallel
        with futures.ThreadPoolExecutor() as ex:
            partial_results = list(ex.map(analysis, filenames))

        # Flatten the list of lists into a single results list
        results = [item for sublist in partial_results for item in sublist]

        return results
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


def csv_writer(results, path):
    logger.info(f"Writing image analysis results to results.csv at {path}.")

    try:
        headers = ["Time", "Name", "Color", "Mean_gray", "Gray"]
        output_file = os.path.join(path, "results.csv")

        with open(output_file, mode="w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            if csvfile.tell() == 0:
                writer.writerow(headers)
            for result in results:
                writer.writerow(result)

        df = pd.read_csv(output_file)
        df_sorted = df.sort_values(by="Time")

        df_sorted.to_csv(output_file, index=False)
        return df_sorted
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
