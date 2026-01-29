import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import sys
import threading

# Assuming gredos2x is installed or its path is in sys.path
from gredos2x.gredos2gpkg import Gredos2GPKG

class GredosExportApp:
    def __init__(self, master):
        self.master = master
        master.title("Gredos to GeoPackage Export")

        # Default paths (can be pre-filled from the original script or left empty)
        # These paths are for demonstration and should be adjusted by the user
        self.gredos_mdb_povezava_default = r"C:\Users\ep5065\OneDrive - Elektro Primorska d.d\GREDOS\Gredos 2026\modeli\26_1_2026\26_1_2026.mdb"
        self.gredos_materiali_povezava_default = r"C:\GredosMO_10\Defaults\material_2000_v10.mdb"
        self.izvozi_v_default = r"C:\Users\ep5065\OneDrive - Elektro Primorska d.d\GREDOS\Gredos 2026\modeli\26_1_2026\referencni_modeli_izvoz.gpkg"

        # --- Gredos MDB Path ---
        tk.Label(master, text="Pot do glavne datoteke Gredos MDB:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.mdb_path_entry = tk.Entry(master, width=70)
        self.mdb_path_entry.grid(row=0, column=1, padx=5, pady=2)
        self.mdb_path_entry.insert(0, self.gredos_mdb_povezava_default)
        tk.Button(master, text="Izberi glavno datoteko Gredos (.mdb)", command=self.browse_mdb).grid(row=0, column=2, padx=5, pady=2)

        # --- Materials MDB Path ---
        tk.Label(master, text="Pot do materialov modela:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.materials_path_entry = tk.Entry(master, width=70)
        self.materials_path_entry.grid(row=1, column=1, padx=5, pady=2)
        self.materials_path_entry.insert(0, self.gredos_materiali_povezava_default)
        tk.Button(master, text="Izberi materiale MDB", command=self.browse_materials_mdb).grid(row=1, column=2, padx=5, pady=2)

        # --- Output GeoPackage Path ---
        tk.Label(master, text="Izvozi v GPKG datoteko:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.gpkg_path_entry = tk.Entry(master, width=70)
        self.gpkg_path_entry.grid(row=2, column=1, padx=5, pady=2)
        self.gpkg_path_entry.insert(0, self.izvozi_v_default)
        tk.Button(master, text="Izberi pot za izvoz (.gpkg)", command=self.browse_gpkg).grid(row=2, column=2, padx=5, pady=2)

        # --- Options ---
        self.pretvori_crs_var = tk.BooleanVar(value=True)
        tk.Checkbutton(master, text="Convert CRS (to EPSG:3912)", variable=self.pretvori_crs_var).grid(row=3, column=0, sticky="w", padx=5, pady=2)
        # For simplicity, set_crs is hardcoded to 'EPSG:3912' as in the original example.
        # A more advanced GUI might offer a dropdown or entry for set_crs.

        # --- Export Button ---
        self.export_button = tk.Button(master, text="Začni izvoz", command=self.start_export_thread)
        self.export_button.grid(row=4, column=0, columnspan=3, pady=10)

        # --- Status / Log Area ---
        tk.Label(master, text="Status / Log:").grid(row=5, column=0, sticky="w", padx=5, pady=2)
        self.log_text = scrolledtext.ScrolledText(master, width=90, height=15, state='disabled')
        self.log_text.grid(row=6, column=0, columnspan=3, padx=5, pady=5)

        # Redirect print statements to the log_text widget
        self.original_stdout = sys.stdout
        sys.stdout = self

    def write(self, text):
        """Writes text to the scrolled text widget and the original stdout."""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END) # Auto-scroll to the end
        self.log_text.config(state='disabled')
        self.original_stdout.write(text) # Also print to console for debugging/logging

    def flush(self):
        """Required for file-like object behavior."""
        self.original_stdout.flush()

    def browse_mdb(self):
        filename = filedialog.askopenfilename(
            title="Select Gredos MDB File",
            filetypes=[("MDB files", "*.mdb"), ("All files", "*.*")]
        )
        if filename:
            self.mdb_path_entry.delete(0, tk.END)
            self.mdb_path_entry.insert(0, filename)

    def browse_materials_mdb(self):
        filename = filedialog.askopenfilename(
            title="Select Materials MDB File",
            filetypes=[("MDB files", "*.mdb"), ("All files", "*.*")]
        )
        if filename:
            self.materials_path_entry.delete(0, tk.END)
            self.materials_path_entry.insert(0, filename)

    def browse_gpkg(self):
        filename = filedialog.asksaveasfilename(
            title="Save Output GeoPackage File",
            defaultextension=".gpkg",
            filetypes=[("GeoPackage files", "*.gpkg"), ("All files", "*.*")]
        )
        if filename:
            self.gpkg_path_entry.delete(0, tk.END)
            self.gpkg_path_entry.insert(0, filename)

    def start_export_thread(self):
        """Starts the export process in a separate thread to keep the GUI responsive."""
        self.export_button.config(state='disabled') # Disable button during export
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END) # Clear previous log
        self.log_text.config(state='disabled')
        self.write("Export process started...\n")

        export_thread = threading.Thread(target=self.run_export)
        export_thread.start()

    def run_export(self):
        """Executes the Gredos2GPKG export logic."""
        mdb_path = self.mdb_path_entry.get()
        materials_path = self.materials_path_entry.get()
        gpkg_output_path = self.gpkg_path_entry.get()
        pretvori_crs = self.pretvori_crs_var.get()
        set_crs = 'EPSG:3912' # Hardcoded as per original example

        if not mdb_path or not materials_path or not gpkg_output_path:
            messagebox.showerror("Error", "All paths must be provided.")
            self.write("Error: All paths must be provided.\n")
            self.export_button.config(state='normal')
            return

        if not os.path.exists(mdb_path):
            messagebox.showerror("Error", f"Gredos MDB file not found: {mdb_path}")
            self.write(f"Error: Gredos MDB file not found: {mdb_path}\n")
            self.export_button.config(state='normal')
            return

        if not os.path.exists(materials_path):
            messagebox.showerror("Error", f"Materials MDB file not found: {materials_path}")
            self.write(f"Error: Materials MDB file not found: {materials_path}\n")
            self.export_button.config(state='normal')
            return

        try:
            self.write(f"Initializing Gredos2GPKG with:\n")
            self.write(f"  MDB: {mdb_path}\n")
            self.write(f"  Materials: {materials_path}\n")
            self.write(f"  Output GPKG: {gpkg_output_path}\n")
            self.write(f"  Convert CRS: {pretvori_crs}\n")
            self.write(f"  Set CRS: {set_crs}\n")

            gredos2gpkg_instance = Gredos2GPKG(
                povezava_mdb=mdb_path,
                pot_materiali=materials_path,
                povezava_gpkg=gpkg_output_path
            )
            self.write("Gredos2GPKG instance created. Starting export...\n")
            gredos2gpkg_instance.pozeni_uvoz(
                show_progress=True,
                pretvori_crs=pretvori_crs,
                set_crs=set_crs
            )
            messagebox.showinfo("Success", "Export completed successfully!")
            self.write("Export completed successfully!\n")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during export: {e}")
            self.write(f"Error during export: {e}\n")
        finally:
            self.export_button.config(state='normal') # Re-enable button

if __name__ == "__main__":
    root = tk.Tk()
    app = GredosExportApp(root)
    root.mainloop()