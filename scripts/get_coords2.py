import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pandas as pd
import os
import sys


class BacteriaColorAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bacteria Color Analysis")

        # Initialize variables
        self.sample_name_var = tk.StringVar()
        self.color_var = tk.StringVar()
        self.image_path = ""
        self.image = None
        self.photo = None
        self.scale_ratio = 1.0
        self.max_image_size = (800, 600)  # Adjust as needed
        self.selections = []  # To store recent selections

        # Determine the appropriate resampling filter
        self.resample_filter = self.get_resample_filter()

        # Setup GUI
        self.setup_gui()

    def get_resample_filter(self):
        """
        Determine the appropriate resampling filter based on Pillow version.
        """
        from PIL import __version__ as PILLOW_VERSION
        from packaging import version

        if version.parse(PILLOW_VERSION) >= version.parse("10.0.0"):
            return Image.Resampling.LANCZOS
        else:
            return Image.ANTIALIAS

    def setup_gui(self):
        # Frames
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        image_frame = tk.Frame(self.root)
        image_frame.pack(side=tk.LEFT, padx=10, pady=10)

        sidebar_frame = tk.Frame(self.root)
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # Control Frame Components
        tk.Label(control_frame, text="Sample Name:").grid(
            row=0, column=0, padx=5, pady=5, sticky=tk.E
        )
        self.sample_name_entry = tk.Entry(
            control_frame, textvariable=self.sample_name_var
        )
        self.sample_name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(control_frame, text="Color:").grid(
            row=1, column=0, padx=5, pady=5, sticky=tk.E
        )
        self.color_entry = tk.Entry(control_frame, textvariable=self.color_var)
        self.color_entry.grid(row=1, column=1, padx=5, pady=5)

        select_image_button = tk.Button(
            control_frame, text="Select Image", command=self.select_image
        )
        select_image_button.grid(row=0, column=2, rowspan=2, padx=10, pady=5)

        # Image Frame Components
        self.canvas = tk.Canvas(
            image_frame,
            width=self.max_image_size[0],
            height=self.max_image_size[1],
            bg="grey",
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Sidebar Frame Components
        tk.Label(sidebar_frame, text="Recent Selections").pack()

        # Updated column titles: 'name', 'color', 'x', 'y'
        columns = ("name", "color", "x", "y")
        self.tree = ttk.Treeview(
            sidebar_frame, columns=columns, show="headings", height=20
        )  # Changed height to 20
        for col in columns:
            self.tree.heading(
                col, text=col.capitalize()
            )  # Capitalize for better readability
            self.tree.column(col, width=80, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

        discard_button = tk.Button(
            sidebar_frame, text="Discard Selected", command=self.discard_selection
        )
        discard_button.pack(pady=5)

        # Save & Exit Button
        save_exit_button = tk.Button(
            sidebar_frame, text="Save & Exit", command=self.save_and_exit
        )
        save_exit_button.pack(pady=5)

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")],
        )
        if file_path:
            self.image_path = file_path
            self.load_and_display_image()

    def load_and_display_image(self):
        try:
            pil_image = Image.open(self.image_path)
            original_size = pil_image.size
            pil_image.thumbnail(self.max_image_size, self.resample_filter)
            self.scale_ratio = (
                original_size[0] / pil_image.size[0],
                original_size[1] / pil_image.size[1],
            )
            self.photo = ImageTk.PhotoImage(pil_image)
            self.canvas.config(width=pil_image.width, height=pil_image.height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            self.canvas.image = self.photo  # Prevent garbage collection
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def on_canvas_click(self, event):
        if not self.image_path:
            messagebox.showwarning("No Image", "Please select an image first.")
            return

        sample_name = self.sample_name_var.get().strip()
        color = self.color_var.get().strip()

        if not sample_name or not color:
            messagebox.showwarning(
                "Input Required", "Please enter both sample name and color."
            )
            return

        # Calculate original coordinates
        orig_x = int(event.x * self.scale_ratio[0])
        orig_y = int(event.y * self.scale_ratio[1])

        # Mark the point on the canvas with a smaller dot
        radius = 3  # Smaller radius for the dot
        self.canvas.create_oval(
            event.x - radius,
            event.y - radius,
            event.x + radius,
            event.y + radius,
            outline="red",
            fill="red",
            width=1,
        )

        # Add to selections list
        selection = {"name": sample_name, "color": color, "x": orig_x, "y": orig_y}
        self.selections.append(selection)
        if len(self.selections) > 20:  # Changed from 10 to 20
            self.selections.pop(0)

        self.update_treeview()
        self.save_to_csv(selection)

    def update_treeview(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insert recent selections
        for sel in self.selections[-20:]:  # Changed from 10 to 20
            self.tree.insert(
                "", tk.END, values=(sel["name"], sel["color"], sel["x"], sel["y"])
            )

    def discard_selection(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select an item to discard.")
            return
        item = selected_item[0]
        values = self.tree.item(item, "values")
        # Find and remove the selection from the list
        for sel in self.selections:
            if (sel["name"], sel["color"], str(sel["x"]), str(sel["y"])) == values:
                self.selections.remove(sel)
                break
        self.update_treeview()
        self.remove_from_csv(values)

    def save_to_csv(self, selection):
        file_exists = os.path.isfile("data.csv")
        df = pd.DataFrame([selection])
        df.to_csv("data.csv", mode="a", header=not file_exists, index=False)

    def remove_from_csv(self, values):
        if not os.path.isfile("data.csv"):
            return
        df = pd.read_csv("data.csv")
        condition = (
            (df["name"] == values[0])
            & (df["color"] == values[1])
            & (df["x"] == int(values[2]))
            & (df["y"] == int(values[3]))
        )
        df = df[~condition]
        df.to_csv("data.csv", index=False)

    def save_and_exit(self):
        # If any final saving is needed, perform here. Currently, selections are saved immediately.
        self.root.destroy()


if __name__ == "__main__":
    # Check for required libraries
    try:
        from packaging import version
    except ImportError:
        print(
            "The 'packaging' library is required. Install it using 'pip install packaging'."
        )
        sys.exit(1)

    root = tk.Tk()
    app = BacteriaColorAnalysisApp(root)
    root.mainloop()
