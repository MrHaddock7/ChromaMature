import tkinter as tk
from tkinter import filedialog
import cv2
import csv
import os

# Initialize the main window
root = tk.Tk()
root.title("Bacteria Color Analysis")

# Variables to store user input
sample_name_var = tk.StringVar()
color_var = tk.StringVar()
image_path_var = tk.StringVar()
coordinates = []


# Function to open an image file
def select_image():
    file_path = filedialog.askopenfilename(
        title="Select Image", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
    )
    if file_path:
        image_path_var.set(file_path)
        print(f"Selected image: {file_path}")


def start_analysis():
    sample_name = sample_name_var.get()
    color = color_var.get()
    image_path = image_path_var.get()

    if not image_path:
        print("Please select an image.")
        return
    if not sample_name or not color:
        print("Please enter sample name and color.")
        return

    run_cv2_window(image_path, sample_name, color)


def run_cv2_window(image_path, sample_name, color):
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print("Could not open image.")
        return

    coordinates.clear()  # Clear previous coordinates

    # Mouse callback function
    def click_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # Store the coordinates in the list
            coordinates.append((x, y))
            print(f"Clicked at: ({x}, {y})")

            # Display the coordinates on the image window
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(image, f"({x},{y})", (x, y), font, 0.5, (255, 0, 0), 2)
            cv2.imshow(window_name, image)

            # Save the data to a CSV file
            file_exists = os.path.isfile("data.csv")
            with open("data.csv", "a", newline="") as csvfile:
                fieldnames = ["Sample Name", "Color", "X", "Y"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(
                    {"Sample Name": sample_name, "Color": color, "X": x, "Y": y}
                )

    window_name = "Image - Press q to quit"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, click_event)

    print("Click on the image to get coordinates. Press 'q' to quit.")

    def update_window():
        cv2.imshow(window_name, image)
        key = cv2.waitKey(20) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
        else:
            root.after(20, update_window)

    update_window()


# GUI components for sample name and color input
control_frame = tk.Frame(root)
control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

sample_name_label = tk.Label(control_frame, text="Sample Name:")
sample_name_label.grid(row=0, column=0, padx=5, pady=5)
sample_name_entry = tk.Entry(control_frame, textvariable=sample_name_var)
sample_name_entry.grid(row=0, column=1, padx=5, pady=5)

color_label = tk.Label(control_frame, text="Color:")
color_label.grid(row=1, column=0, padx=5, pady=5)
color_entry = tk.Entry(control_frame, textvariable=color_var)
color_entry.grid(row=1, column=1, padx=5, pady=5)

# Buttons for selecting image and starting analysis
button_frame = tk.Frame(root)
button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

open_button = tk.Button(button_frame, text="Select Image", command=select_image)
open_button.pack(side=tk.LEFT, padx=5)

start_button = tk.Button(button_frame, text="Start Analysis", command=start_analysis)
start_button.pack(side=tk.LEFT, padx=5)

# Start the GUI event loop
root.mainloop()
