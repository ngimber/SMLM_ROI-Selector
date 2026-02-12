import numpy as np
import matplotlib.pyplot as plt
from tkinter.filedialog import askopenfilenames
from tkinter import messagebox
import tkinter as tk
from matplotlib.widgets import RectangleSelector, PolygonSelector, LassoSelector
from matplotlib.widgets import Button as MPLButton
from matplotlib.widgets import RadioButtons, TextBox
import matplotlib.patches as patches
from matplotlib.widgets import Slider
from matplotlib.path import Path
import os
import csv
import pandas as pd

# Global variables
channel = 1
pixNM = 40
selectionMode = "box"
operationMode = "select"
saveMode = "combined"  # combined or separate
navMode = "select"  # select or pan
file = None
table = None
x = None
y = None
binned = None
all_selected_indices = []
all_roi_indices = []  # Store indices for each ROI separately
roi_patches = []
x1 = x2 = y1 = y2 = 0
polygon_verts = []
contrast = 1
contrast0 = 1
output_folder = None
row1 = None
pan_active = False
lasso_active = False
lasso_verts = []

# Remove matplotlib toolbar
plt.rcParams['toolbar'] = 'None'

# Scientific styling
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.linewidth'] = 1.2
plt.rcParams['axes.labelweight'] = 'normal'
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['axes.labelsize'] = 10

# Create main figure with professional styling
fig = plt.figure(figsize=(15, 9), facecolor='#f5f5f5')
gs = fig.add_gridspec(12, 12, left=0.05, right=0.98, bottom=0.15, top=0.95, wspace=0.4, hspace=0.5)

# Main image axis - centered
ax = fig.add_subplot(gs[1:10, 2:11])
ax.set_facecolor('#ffffff')
im = ax.imshow(np.zeros((100, 100)), cmap=plt.get_cmap('gray'), origin="upper")
ax.text(0.5, 0.5, 'Click "Load File" to start', ha='center', va='center', 
        transform=ax.transAxes, fontsize=12, color='#555555', weight='normal')
ax.set_title("Click 'Load File' button to start", color='#333333', fontsize=11, pad=10)


# Load file function
def load_file_gui(event):
    global file, table, x, y, binned, channel, pixNM, contrast, contrast0, output_folder, row1
    global all_selected_indices, all_roi_indices, roi_patches, selectionMode
    
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    fileList = askopenfilenames(filetypes=(("SD file", "*.txt"),("ThunderSTORM loc file", "*.csv"),
                                              ("All files", "*.*") ),title="select localization files")
    root.destroy()
    
    if not fileList:
        return
    
    file = fileList
    all_selected_indices = []
    all_roi_indices = []
    roi_patches = []
    
    # Load data
    if (file[0].endswith(".txt")):
        table=pd.read_table(file[0],header=None, skiprows=1,sep=" ")
        if (table.shape[1]==7):
            headers=["x short [nm]","y short [nm]", "I short", "frame","x long [nm]","y long [nm]", "I long"]
        if (table.shape[1]==8):
            headers=["x short [nm]","y short [nm]", "I short", "frame","x long [nm]","y long [nm]", "I long", "channel"]
        table.columns=headers
        
        with open(file[0], newline='') as f:
            reader = csv.reader(f)
            row1 = next(reader)
    else:
        table=pd.read_csv(file[0],sep=",")
    
    # Create output folder
    output_folder = os.path.join(os.path.dirname(file[0]), "ROI_processed")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Initialize selector for box mode
    selectionMode = "box"
    radio.set_active(0)  # Set Box as active
    
    update_image()
    initialize_selector()
    print(f"Loaded: {os.path.basename(file[0])}")


def update_image():
    global x, y, binned, contrast, contrast0, im
    
    if file is None or table is None:
        return
    
    # Get data based on channel
    if (file[0].endswith(".txt")):
        if (table.shape[1]==8):
            x_data = table[table["channel"]==channel]["x short [nm]"]
            y_data = table[table["channel"]==channel]["y short [nm]"]
        else: 
            x_data = table["x short [nm]"]
            y_data = table["y short [nm]"]
    else:
        x_data = table["x [nm]"]
        y_data = table["y [nm]"]
    
    if len(x_data) ==0 or len(y_data) == 0:
        print(f"Warning: No data for channel {channel}")
        return
    
    x = x_data
    y = y_data
    
    # Create histogram
    binned=np.rot90(np.flip(np.histogram2d(x, y, bins=[int((np.max(x)-1)/pixNM),int((np.max(y)-1)/pixNM)],
                                            range=np.array([(0,np.max(x)-1), (0, np.max(y)-1)]))[0].astype(float),axis=1))
    
    contrast = np.max(binned)
    contrast0 = contrast
    
    # Update image
    ax.clear()
    im = ax.imshow(binned, vmax=contrast, cmap=plt.get_cmap('gray'), origin="upper")
    
    # Redraw ROI patches
    for patch in roi_patches:
        ax.add_patch(patch)
    
    op_text = "SELECT" if operationMode == "select" else "REMOVE"
    ax.set_title(f"{op_text} mode: {selectionMode.upper()}. Total: {len(all_selected_indices)} locs | {os.path.basename(file[0])}", 
                 color='red', fontsize=10)
    
    # Update contrast slider
    samp.valmax = contrast
    samp.ax.set_xlim(0, contrast)
    samp.set_val(contrast)
    
    plt.draw()


def update_channel(text):
    global channel
    try:
        channel = int(text)
        update_image()
        print(f"Channel: {channel}")
    except:
        print("Invalid channel")


def update_pixelsize(text):
    global pixNM
    try:
        pixNM = int(text)
        update_image()
        print(f"Pixel size: {pixNM} nm")
    except:
        print("Invalid pixel size")


# Callback functions
def line_select_callback(eclick, erelease):
    global x1, x2, y1, y2
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    print("(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))


def polygon_select_callback(verts):
    global polygon_verts
    polygon_verts = verts
    print(f"Polygon with {len(verts)} vertices - Press ENTER to add or double-click to complete")


def lasso_select_callback(verts):
    global polygon_verts
    # Convert to list if it's a numpy array
    if hasattr(verts, 'tolist'):
        polygon_verts = verts.tolist()
    else:
        polygon_verts = list(verts)
    print(f"Freehand: {len(polygon_verts)} points captured")
    if len(polygon_verts) > 2:
        print("Press ENTER to add this ROI")
    else:
        print("Draw a larger freehand ROI (need at least 3 points)")


def initialize_selector():
    global selectionMode
    if selectionMode == "box":
        # Box selector with RED rectangle
        props = dict(facecolor='none', edgecolor='#d62728', linewidth=2, alpha=0.8)
        toggle_selector.RS = RectangleSelector(ax, line_select_callback,
                                               useblit=False,
                                               button=[1, 3],
                                               minspanx=5, minspany=5,
                                               spancoords='pixels',
                                               interactive=True,
                                               props=props)
        toggle_selector.RS.set_active(True)
    elif selectionMode == "polygon":
        # Polygon with RED visible lines - completes on double-click or first point click
        props = dict(color='#d62728', linewidth=2, alpha=0.8)
        toggle_selector.PS = PolygonSelector(ax, polygon_select_callback,
                                             useblit=False,
                                             props=props,
                                             handle_props=dict(markersize=8, markerfacecolor='#d62728'))
        toggle_selector.PS.set_active(True)
    elif selectionMode == "freehand":
        # Freehand lasso selector - click and drag to draw, releases to complete
        toggle_selector.LS = LassoSelector(ax, lasso_select_callback, button=1)
        # Set line properties after creation
        if hasattr(toggle_selector.LS, 'line'):
            toggle_selector.LS.line.set_color('#d62728')
            toggle_selector.LS.line.set_linewidth(2)
        toggle_selector.LS.set_active(True)
        print("Freehand mode: Click and HOLD, DRAG to draw your ROI, then RELEASE and press ENTER")


def switch_mode(label):
    global selectionMode, polygon_verts
    selectionMode = label.lower()
    polygon_verts = []  # Clear previous vertices
    
    if file is None:
        print("Please load a file first")
        return
    
    # Deactivate all selectors
    if hasattr(toggle_selector, 'RS'):
        toggle_selector.RS.set_active(False)
        toggle_selector.RS.set_visible(False)
    if hasattr(toggle_selector, 'PS'):
        toggle_selector.PS.set_active(False)
        toggle_selector.PS.set_visible(False)
    if hasattr(toggle_selector, 'LS'):
        toggle_selector.LS.set_active(False)
        toggle_selector.LS.set_visible(False)
    
    # Redraw
    update_image()
    
    # Create new selector
    initialize_selector()
    print(f"Drawing mode: {selectionMode.upper()}")


def switch_operation_mode(label):
    global operationMode
    operationMode = label.lower()
    op_text = "SELECT" if operationMode == "select" else "REMOVE"
    if file is not None:
        ax.set_title(f"{op_text} mode: {selectionMode.upper()}. Total: {len(all_selected_indices)} locs | {os.path.basename(file[0])}", 
                     color='red', fontsize=10)
        plt.draw()
    print(f"Operation: {operationMode.upper()}")


def toggle_selector(event):
    global all_selected_indices, roi_patches
    
    if file is None:
        print("Please load a file first")
        return
    
    # Handle activation/deactivation
    if event is not None and hasattr(event, 'key'):
        if selectionMode == "box":
            if event.key in ['Q', 'q'] and hasattr(toggle_selector, 'RS') and toggle_selector.RS.active:
                toggle_selector.RS.set_active(False)
                return
            if event.key in ['A', 'a'] and hasattr(toggle_selector, 'RS') and not toggle_selector.RS.active:
                toggle_selector.RS.set_active(True)
                return
        elif selectionMode == "polygon":
            if event.key in ['Q', 'q'] and hasattr(toggle_selector, 'PS') and toggle_selector.PS.active:
                toggle_selector.PS.set_active(False)
                return
            if event.key in ['A', 'a'] and hasattr(toggle_selector, 'PS') and not toggle_selector.PS.active:
                toggle_selector.PS.set_active(True)
                return
        elif selectionMode == "freehand":
            if event.key in ['Q', 'q'] and hasattr(toggle_selector, 'LS'):
                toggle_selector.LS.set_active(False)
                return
            if event.key in ['A', 'a'] and hasattr(toggle_selector, 'LS'):
                toggle_selector.LS.set_active(True)
                return
        
        # Process ROI on Enter
        if event.key not in ['enter', 'return']:
            return
    
    # Get indices based on selection mode and operation mode
    if selectionMode == "box":
        rect = patches.Rectangle((x1,y1),abs(x2-x1),abs(y2-y1),linewidth=2,edgecolor='r',facecolor='none')
        ax.add_patch(rect)
        roi_patches.append(rect)
        
        if (file[0].endswith(".txt")):
            x_= table["x short [nm]"]
            y_= table["y short [nm]"]
            if operationMode == "select":
                selectedIndex=(((x_.values>(x1)*pixNM)*(x_.values<(x2+1)*pixNM)*(y_.values>(y1)*pixNM)*(y_.values<(y2+1)*pixNM))*table.index.values).tolist()
            else:
                selectedIndex=(((x_.values<(x1)*pixNM)+(x_.values>(x2+1)*pixNM)+(y_.values<(y1)*pixNM)+(y_.values>(y2+1)*pixNM))*table.index.values).tolist()
        else:
            if operationMode == "select":
                selectedIndex=(((x.values>(x1)*pixNM)*(x.values<(x2+1)*pixNM)*(y.values>(y1)*pixNM)*(y.values<(y2+1)*pixNM))*table.index.values).tolist()
            else:
                selectedIndex=(((x.values<(x1)*pixNM)+(x.values>(x2+1)*pixNM)+(y.values<(y1)*pixNM)+(y.values>(y2+1)*pixNM))*table.index.values).tolist()
    else:
        # Check if polygon_verts has data
        if not polygon_verts or len(polygon_verts) < 3:
            if selectionMode == "freehand":
                print(f"No freehand ROI captured. Click-HOLD-DRAG to draw, then RELEASE mouse.")
            else:
                print(f"No valid polygon drawn. Click points to create polygon, double-click to close.")
            return
            
        poly = patches.Polygon(polygon_verts, linewidth=2, edgecolor='r', facecolor='none', closed=True)
        ax.add_patch(poly)
        roi_patches.append(poly)
        
        path = Path(polygon_verts)
        if (file[0].endswith(".txt")):
            x_= table["x short [nm]"]
            y_= table["y short [nm]"]
            points = np.column_stack((x_.values/pixNM, y_.values/pixNM))
        else:
            points = np.column_stack((x.values/pixNM, y.values/pixNM))
        
        if operationMode == "select":
            mask = path.contains_points(points)
        else:
            mask = ~path.contains_points(points)
        selectedIndex = (mask * table.index.values).tolist()
    
    selectedIndex = [int(i) for i in selectedIndex if i > 0]
    all_selected_indices.extend(selectedIndex)
    all_selected_indices = list(set(all_selected_indices))
    
    # Store this ROI separately for individual file export option
    all_roi_indices.append(selectedIndex)
    
    op_text = "SELECT" if operationMode == "select" else "REMOVE"
    ax.set_title(f"{op_text} mode: {selectionMode.upper()}. Added {len(selectedIndex)} | Total: {len(all_selected_indices)} locs | {os.path.basename(file[0])}", 
                 color='#333333', fontsize=11, pad=10)
    print(f"Added ROI #{len(all_roi_indices)}: {len(selectedIndex)} locs. Total: {len(all_selected_indices)}")
    plt.draw()


def save_data(event):
    global all_selected_indices, all_roi_indices, table, saveMode
    
    if file is None:
        print("Please load a file first!")
        return
    
    if len(all_selected_indices) == 0:
        print("No ROIs selected!")
        return
    
    print(f"Saving in {saveMode.upper()} mode...")
    
    base_name = os.path.basename(file[0])
    suffix = "_selected" if operationMode == "select" else "_cropped"
    
    if saveMode == "combined":
        # Save all ROIs in one file
        selectedTable = table.iloc[all_selected_indices]
        
        counter = 0
        if file[0].endswith(".txt"):
            fname = os.path.join(output_folder, base_name[:base_name.find(".txt")] + suffix + str(counter) + ".txt")
            while os.path.isfile(fname):
                counter += 1
                fname = os.path.join(output_folder, base_name[:base_name.find(".txt")] + suffix + str(counter) + ".txt")
            np.savetxt(fname, selectedTable.values, comments="", header=row1[0], fmt='%f')
        else:
            fname = os.path.join(output_folder, base_name[:base_name.find(".csv")] + suffix + str(counter) + ".csv")
            while os.path.isfile(fname):
                counter += 1
                fname = os.path.join(output_folder, base_name[:base_name.find(".csv")] + suffix + str(counter) + ".csv")
            selectedTable.to_csv(fname, index=None)
        
        print(f"✓ Saved {len(all_selected_indices)} locs from {len(roi_patches)} ROI(s) as {fname}")
    
    else:  # separate mode
        # Save each ROI in a separate file
        saved_files = []
        for roi_num, roi_indices in enumerate(all_roi_indices, 1):
            selectedTable = table.iloc[roi_indices]
            
            if file[0].endswith(".txt"):
                fname = os.path.join(output_folder, base_name[:base_name.find(".txt")] + suffix + f"_ROI{roi_num}.txt")
                np.savetxt(fname, selectedTable.values, comments="", header=row1[0], fmt='%f')
            else:
                fname = os.path.join(output_folder, base_name[:base_name.find(".csv")] + suffix + f"_ROI{roi_num}.csv")
                selectedTable.to_csv(fname, index=None)
            
            saved_files.append(fname)
            print(f"  ✓ ROI #{roi_num}: {len(roi_indices)} locs → {os.path.basename(fname)}")
        
        print(f"✓ Saved {len(all_roi_indices)} separate ROI files")
    
    print("You can now load a new file or continue working.")


def clear_rois(event):
    global all_selected_indices, all_roi_indices, roi_patches
    
    if file is None:
        return
    
    all_selected_indices = []
    all_roi_indices = []
    for patch in roi_patches:
        patch.remove()
    roi_patches = []
    
    op_text = "SELECT" if operationMode == "select" else "REMOVE"
    ax.set_title(f"{op_text} mode: {selectionMode.upper()}. Total: 0 locs | {os.path.basename(file[0])}", 
                 color='#333333', fontsize=11, pad=10)
    print("Cleared all ROIs")
    plt.draw()


def zoom_image(factor):
    """Zoom in or out by adjusting axis limits"""
    if binned is None:
        return
    
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    x_center = (xlim[0] + xlim[1]) / 2
    y_center = (ylim[0] + ylim[1]) / 2
    
    x_range = (xlim[1] - xlim[0]) / factor
    y_range = (ylim[1] - ylim[0]) / factor
    
    ax.set_xlim([x_center - x_range/2, x_center + x_range/2])
    ax.set_ylim([y_center - y_range/2, y_center + y_range/2])
    
    fig.canvas.draw_idle()  # Use draw_idle for better performance


# Pan navigation with mouse drag
pan_start = None

def on_mouse_press(event):
    global pan_start, pan_active
    if event.inaxes != ax or not pan_active:
        return
    pan_start = (event.xdata, event.ydata)

def on_mouse_release(event):
    global pan_start
    pan_start = None

def on_mouse_move(event):
    global pan_start
    if pan_start is None or event.inaxes != ax or not pan_active:
        return
    
    dx = pan_start[0] - event.xdata
    dy = pan_start[1] - event.ydata
    
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    ax.set_xlim([xlim[0] + dx, xlim[1] + dx])
    ax.set_ylim([ylim[0] + dy, ylim[1] + dy])
    
    fig.canvas.draw_idle()  # Use draw_idle for better performance

def toggle_pan(event):
    global pan_active
    pan_active = not pan_active
    
    if pan_active:
        # Deactivate selectors when pan is active
        if hasattr(toggle_selector, 'RS'):
            toggle_selector.RS.set_active(False)
        if hasattr(toggle_selector, 'PS'):
            toggle_selector.PS.set_active(False)
        if hasattr(toggle_selector, 'LS'):
            toggle_selector.LS.set_active(False)
        btn_pan.label.set_text('Mouse: Navigate')
        btn_pan.color = '#27ae60'
        btn_pan.hovercolor = '#229954'
        print("Mouse navigation ON - Click and drag to pan image")
    else:
        # Reactivate selector
        if hasattr(toggle_selector, 'RS'):
            toggle_selector.RS.set_active(True)
        if hasattr(toggle_selector, 'PS'):
            toggle_selector.PS.set_active(True)
        if hasattr(toggle_selector, 'LS'):
            toggle_selector.LS.set_active(True)
        btn_pan.label.set_text('Mouse: Select ROI')
        btn_pan.color = '#95a5a6'
        btn_pan.hovercolor = '#7f8c8d'
        print("Mouse selection active - Draw ROIs with mouse")
    
    fig.canvas.draw_idle()

def switch_save_mode(label):
    global saveMode
    saveMode = label.lower()
    print(f"Save mode: {saveMode.upper()}")


def show_help(event):
    op_mode_text = "SELECT (keep selected)" if operationMode == "select" else "REMOVE (delete selected)"
    save_mode_text = "COMBINED (all ROIs → one file)" if saveMode == "combined" else "SEPARATE (each ROI → own file)"
    help_text = f"""ROI SELECTION TOOL - HELP

Current Settings:
  Operation: {op_mode_text}
  Save Mode: {save_mode_text}

CONTROLS:
• Load File: Browse localization file
• Channel: Display channel (press Enter)
• Pixel (nm): Pixel size (press Enter)
• Contrast: Adjust brightness
• Operation: SELECT (keep) / REMOVE (delete)
• Draw Mode: Box / Polygon / Freehand
• Zoom In/Out: Zoom by 20%
• Mouse Mode: Toggle between navigation and ROI selection
• Save Mode: Combined / Separate files

DRAWING MODES:
• Box: Click and drag rectangle
• Polygon: Click points, double-click to close
• Freehand: Click and HOLD, drag to draw, release then press ENTER

WORKFLOW:
1. Load File → select data
2. Adjust Channel, Pixel size
3. Choose Operation (Select/Remove)
4. Choose Draw Mode
5. Set Mouse Mode to "Select ROI"
6. Draw ROI:
   - Box: Drag → press ENTER
   - Polygon: Click points → double-click → press ENTER
   - Freehand: Click and HOLD → drag to draw → release → press ENTER
7. Repeat for multiple ROIs
8. Choose Save Mode
9. Click Save

SHORTCUTS:
ENTER - Add ROI (Box/Polygon)
Double-Click - Complete Polygon
Q - Deactivate tool
A - Activate tool

MOUSE MODES:
• Select ROI - Draw ROIs with mouse
• Navigate - Drag to pan zoomed image

OUTPUT:
• Folder: ROI_processed/
• Files: _selected# or _cropped#
• ROIs shown in RED

Contact: niclas.gimber@charite.de
"""
    
    root_help = tk.Tk()
    root_help.withdraw()
    root_help.attributes("-topmost", True)
    messagebox.showinfo("ROI Tool - Help", help_text)
    root_help.destroy()


# UI Elements on left panel - Professional Scientific Styling
# Load File button
ax_load = plt.axes([0.02, 0.88, 0.13, 0.05])
ax_load.patch.set_facecolor('#ffffff')
btn_load = MPLButton(ax_load, 'Load File', color='#34495e', hovercolor='#2c3e50')
btn_load.label.set_fontsize(10)
btn_load.label.set_weight('bold')
btn_load.on_clicked(load_file_gui)

# Channel textbox
ax_channel = plt.axes([0.02, 0.79, 0.13, 0.04])
ax_channel.patch.set_facecolor('#ffffff')
fig.text(0.02, 0.84, 'Channel:', fontsize=10, weight='bold', color='#2c3e50')
textbox_channel = TextBox(ax_channel, '', initial=str(channel))
textbox_channel.on_submit(update_channel)

# Pixel size textbox
ax_pixsize = plt.axes([0.02, 0.7, 0.13, 0.04])
ax_pixsize.patch.set_facecolor('#ffffff')
fig.text(0.02, 0.75, 'Pixel (nm):', fontsize=10, weight='bold', color='#2c3e50')
textbox_pixsize = TextBox(ax_pixsize, '', initial=str(pixNM))
textbox_pixsize.on_submit(update_pixelsize)

# Operation mode radio buttons
ax_opmode = plt.axes([0.02, 0.54, 0.13, 0.12])
ax_opmode.patch.set_facecolor('#ffffff')
fig.text(0.02, 0.67, 'Operation:', fontsize=10, weight='bold', color='#2c3e50')
radio_opmode = RadioButtons(ax_opmode, ('Select', 'Remove'), active=0)
radio_opmode.on_clicked(switch_operation_mode)

# Drawing mode selector
ax_mode = plt.axes([0.02, 0.36, 0.13, 0.16])
ax_mode.patch.set_facecolor('#ffffff')
fig.text(0.02, 0.53, 'Draw Mode:', fontsize=10, weight='bold', color='#2c3e50')
radio = RadioButtons(ax_mode, ('Box', 'Polygon', 'Freehand'), active=0)
radio.on_clicked(switch_mode)

# Zoom buttons
fig.text(0.02, 0.32, 'Zoom:', fontsize=10, weight='bold', color='#2c3e50')
btn_zoom_in = MPLButton(plt.axes([0.02, 0.26, 0.06, 0.04]), 'In', color='#16a085', hovercolor='#138d75')
btn_zoom_in.label.set_fontsize(9)
btn_zoom_in.on_clicked(lambda event: zoom_image(1.2))

btn_zoom_out = MPLButton(plt.axes([0.09, 0.26, 0.06, 0.04]), 'Out', color='#16a085', hovercolor='#138d75')
btn_zoom_out.label.set_fontsize(9)
btn_zoom_out.on_clicked(lambda event: zoom_image(0.8))

# Pan button
fig.text(0.02, 0.22, 'Mouse Mode:', fontsize=10, weight='bold', color='#2c3e50')
ax_pan = plt.axes([0.02, 0.16, 0.13, 0.04])
ax_pan.patch.set_facecolor('#ffffff')
btn_pan = MPLButton(ax_pan, 'Mouse: Select ROI', color='#95a5a6', hovercolor='#7f8c8d')
btn_pan.label.set_fontsize(9)
btn_pan.on_clicked(toggle_pan)

# Save mode radio buttons
ax_savemode = plt.axes([0.02, 0.03, 0.13, 0.10])
ax_savemode.patch.set_facecolor('#ffffff')
fig.text(0.02, 0.14, 'Save Mode:', fontsize=10, weight='bold', color='#2c3e50')
radio_savemode = RadioButtons(ax_savemode, ('Combined', 'Separate'), active=0)
radio_savemode.on_clicked(switch_save_mode)

# Bottom buttons - Professional styling
bcut = MPLButton(plt.axes([0.75, 0.02, 0.10, 0.04]), 'Save', color='#27ae60', hovercolor='#229954')
bcut.label.set_fontsize(10)
bcut.label.set_weight('bold')
bcut.on_clicked(save_data)

bclear = MPLButton(plt.axes([0.63, 0.02, 0.10, 0.04]), 'Clear ROIs', color='#c0392b', hovercolor='#a93226')
bclear.label.set_fontsize(10)
bclear.label.set_weight('bold')
bclear.on_clicked(clear_rois)

bhelp = MPLButton(plt.axes([0.51, 0.02, 0.10, 0.04]), 'Help', color='#2980b9', hovercolor='#21618c')
bhelp.label.set_fontsize(10)
bhelp.label.set_weight('bold')
bhelp.on_clicked(show_help)

# Email
fig.text(0.01, 0.005, 'niclas.gimber@charite.de', fontsize=9, color='#555555', 
         verticalalignment='bottom', horizontalalignment='left', style='italic')

# Contrast slider - centered below the image
axamp = plt.axes([0.35, 0.08, 0.45, 0.02])
fig.text(0.32, 0.105, 'Contrast:', fontsize=9, weight='bold')
samp = Slider(axamp, '', 0, contrast, valinit=contrast0)

def update_contrast(val):
    global contrast
    contrast = (samp.val)**0.5
    if binned is not None:
        im.set_clim(vmax=contrast)
        plt.draw()

samp.on_changed(update_contrast)

# Unified mouse button handler
def on_mouse_button(event):
    global pan_start
    
    # Don't interfere with freehand mode - LassoSelector needs direct mouse access
    if selectionMode == "freehand" and not pan_active:
        return
    
    # Handle double-click for polygon completion
    if event.dblclick and event.inaxes == ax and not pan_active:
        if selectionMode == "polygon" and hasattr(toggle_selector, 'PS'):
            if hasattr(toggle_selector.PS, '_xs') and len(toggle_selector.PS._xs) > 2:
                verts = list(zip(toggle_selector.PS._xs, toggle_selector.PS._ys))
                polygon_select_callback(verts)
                toggle_selector.PS.set_active(False)
                toggle_selector.PS.set_active(True)
                print("Polygon completed via double-click - Press ENTER to add ROI")
                return
    
    # Handle pan mode on single click
    if event.inaxes == ax and pan_active and not event.dblclick:
        pan_start = (event.xdata, event.ydata)

# Connect unified mouse handler
fig.canvas.mpl_connect('button_press_event', on_mouse_button)

# Connect keyboard events
plt.connect('key_press_event', toggle_selector)

# Connect pan navigation mouse events
fig.canvas.mpl_connect('button_release_event', on_mouse_release)
fig.canvas.mpl_connect('motion_notify_event', on_mouse_move)

plt.show()
