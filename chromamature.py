from scripts.image_analysis import *
from scripts.plots import *
from scripts.stat_test import *
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
    yrange,
    interval_size,
    votes,
    jump_size,
    clean_data,
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

        # Clean data not viable
        if clean_data:
            image_results = clean_data(
                image_results,
                interval_size,
                votes,
                time_interval,
                interval_jump=jump_size,
            )

        logger.info("Image analysis complete, generating plots.")

        if yrange is None:
            yrange = scatterplot_range(image_results)

        for name in image_results["Name"].unique():
            scatterplot(
                image_results,
                name,
                output_path=f"{output_path}/scatterplots",
                yrange=yrange,
            )

        label, conf_interval = boxplot(
            image_results, output_path=f"{output_path}/boxplots"
        )

        with open(f"{output_path}/bootstrap_results.txt", "w") as f:
            # Write header
            f.write("name, mean, conf_in\n")
            for lab, ci in zip(label, conf_interval):
                # ci is structured as ((lower, upper), mean)
                conf_values, mean_value = ci
                conf_str = f"[{conf_values[0]}, {conf_values[1]}]"
                f.write(f"{lab}, {mean_value}, {conf_str}\n")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":

    logger.info("Parsing arguments and starting script.")
    parser = argparse.ArgumentParser(
        description="Processes an directory of images to find halftime values of the color maturation"
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
        help="If you want to run the image analysis using parallelization (recommended)",
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

    parser.add_argument(
        "-yr",
        "--yrange",
        help="Determines the y-range for the scatter plots. Could be either a tuple, (ymin, ymax) or an integer",
        default=None,
    )

    parser.add_argument(
        "-iz",
        "--interval_size",
        help="The interval size when cleaning the data",
        default=20,
    )

    parser.add_argument(
        "-v", "--votes", help="Total amount of votes for it to be an outlier", default=4
    )

    parser.add_argument(
        "-jz",
        "--jump_size",
        help="Size of the jump in relation of the readingframe for data cleaning, e.g -jz 5 will result in a 20%% jump of the reading frame relative to the length of the reading frame",
        default=5,
    )

    parser.add_argument(
        "-cd",
        "--clean_data",
        help="Cleans data (not recommended yet)",
        default=False,
        action="store_true",
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
        yrange=args.yrange,
        jump_size=args.jump_size,
        votes=args.votes,
        interval_size=args.interval_size,
        clean_data=args.clean_data,
    )
