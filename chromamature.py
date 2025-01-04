from scripts.image_analysis import *
from scripts.plots import *
import argparse
import os
import logging


def main(
    coords_path,
    output_path,
    im_path,
    run_name,
    parallel,
    time_interval,
    roi_size,
):

    logging.getLogger("matplotlib").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("chromamature.log")],
    )

    logger.info("Starting main function.")
    output_path = f"{output_path}/{run_name}"

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if not os.path.exists(f"{output_path}/scatterplots"):
        os.makedirs(f"{output_path}/scatterplots")
    if not os.path.exists(f"{output_path}/boxplots"):
        os.makedirs(f"{output_path}/boxplots")

    try:
        if parallel:
            logger.info("Running image analysis in parallel mode.")
            image_results = process_images_parallel(
                im_path, coords_path, time_interval, roi_size
            )
        else:
            logger.info("Running image analysis in sequential mode.")
            image_results = process_images(
                im_path, coords_path, time_interval, roi_size
            )

        logger.info("Image analysis complete, writing results to csv.")
        image_results = csv_writer(image_results, output_path)
        logger.info("Image analysis complete, generating plots.")
        for name in image_results["Name"].unique():
            scatterplot(image_results, name, output_path=f"{output_path}/scatterplots")

        boxplot(image_results, output_path=f"{output_path}/boxplots")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":

    logger.info("Parsing arguments and starting script.")
    parser = argparse.ArgumentParser(
        description="Processes an directory of images to find halftime values"
    )

    parser.add_argument(
        "-c",
        "--coords",
        help="Path to the coords csv file",
        required=True,
        type=str,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path to the runs output directory",
        required=True,
        type=str,
    )

    parser.add_argument(
        "-ip",
        "--impath",
        help="Path to the sorted image directory",
        required=True,
        type=str,
    )

    parser.add_argument(
        "-n",
        "--name",
        help="Name the run for better structure",
        default="image_analysis",
        type=str,
    )

    parser.add_argument(
        "-p",
        "--parallel",
        help="If you want to run the image analysis using parallelization (recomended)",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-t",
        "--time",
        help="Time interval between the pictures",
        required=True,
        type=int,
    )

    parser.add_argument(
        "-r",
        "--roi_size",
        help="Choose the radius of pixels around each coordinate",
        default=5,
        type=int,
    )

    args = parser.parse_args()

    main(
        coords_path=args.coords,
        output_path=args.output,
        im_path=args.impath,
        run_name=args.name,
        parallel=args.parallel,
        time_interval=args.time,
        roi_size=args.roi_size,
    )
