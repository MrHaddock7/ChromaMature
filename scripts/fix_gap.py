import pandas as pd
import numpy as np
import ast


def fix_gap(csv_path, t_start=865, t_stop=980, t_onward=980):
    df = pd.read_csv(csv_path)

    for sample in df["Name"].unique():
        sample_df = df[df["Name"] == sample]
        grayscale_shift_db = sample_df[
            (sample_df["Time"] >= t_start - 5) & (sample_df["Time"] <= t_stop)
        ]["Mean_gray"].tolist()

        large_gray = []
        small_gray = [grayscale_shift_db[0]]

        for i in range(len(grayscale_shift_db[1:])):
            if grayscale_shift_db[i] > small_gray[0] + 1:
                large_gray.append(grayscale_shift_db[i])
            else:
                small_gray.append(grayscale_shift_db[i])

        change = np.mean(large_gray) - np.mean(small_gray)

        for i in range(865, 5755, 5):

            gray_str = df.loc[(df["Name"] == sample) & (df["Time"] == i), "gray"].values
            gray_list = ast.literal_eval(gray_str[0])

            df.loc[(df["Name"] == sample) & (df["Time"] == i), "Mean_gray"] = (
                df.loc[(df["Name"] == sample) & (df["Time"] == i), "Mean_gray"].values
                - change
            )

            adjusted_gray_list = [x - change for x in gray_list]

            df.loc[(df["Name"] == sample) & (df["Time"] == i), "gray"] = str(
                adjusted_gray_list
            )

    df = df.sort_values(by="Time")
    df.to_csv()


fix_gap()
