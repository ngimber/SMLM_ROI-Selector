# ROI Selection Tool for Microscopy

A Python-based GUI application for selecting and filtering regions of interest (ROI) from single-molecule localization microscopy data.

## Features

- **Multiple Drawing Modes**: Box, Polygon, and Freehand selections
- **Flexible Operations**: SELECT (keep) or REMOVE (delete) localized molecules in ROI
- **Multiple File Formats**: ThunderSTORM (.csv) and SDmixer (.txt) localization data
- **Save Options**: Combined (all ROIs in one file) or Separate (each ROI in individual file)
- **Interactive Controls**: 
  - Zoom in/out
  - Contrast adjustment
  - Pan navigation
  - Keyboard shortcuts

## Requirements

- Python 3.8+
- numpy
- matplotlib
- pandas

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

```bash
python smlm_roi_selector.py
```

### Workflow

1. **Load File**: Click "Load File" → Select your SDmixer (.txt) or ThunderSTORM (.csv)
2. **Adjust Settings**: 
   - Channel: Select the channel to display
   - Pixel size: Set pixel size in nm (default: 40 nm)
3. **Set Operation**:
   - **SELECT**: Keep molecules within ROI
   - **REMOVE**: Delete molecules within ROI
4. **Draw ROI**:
   - Choose Draw Mode: Box / Polygon / Freehand
   - Draw on the image
   - Press **ENTER** to confirm
   - Repeat for multiple ROIs
5. **Save**:
   - Choose Save Mode: Combined or Separate
   - Click **Save**
   - Output saved in `ROI_processed/` folder

### Example: Filter ThunderSTORM Data by Region

```
1. Export all localizations from ThunderSTORM → my_data.csv
2. Run: python smlm_roi_selector.py
3. Load File → select my_data.csv
4. Draw rectangular ROI around region of interest
5. Press ENTER
6. Set Operation: SELECT
7. Set Save Mode: Combined
8. Click Save
9. Output: my_data_selected0.csv (only localizations inside ROI)
```

### Drawing Modes

- **Box**: Click and drag to create rectangular selection
- **Polygon**: Click points to create polygon, double-click or first point to close
- **Freehand**: Click-HOLD, drag to draw, release mouse, press ENTER

### Mouse Navigation

Toggle "Mouse: Navigate" to pan zoomed images without drawing ROIs.

## File Support

### Input Files
- **ThunderSTORM**: CSV format with columns `x [nm]`, `y [nm]`, `intensity [counts]`, etc.
- **SDmixer**: TXT format (space-separated) with columns `x short [nm]`, `y short [nm]`, etc.

### Output Files
- Located in `ROI_processed/` subfolder of input file location
- Filename format: `[original]_selected0.csv` or `[original]_cropped0.csv`
- Auto-numbered to prevent file overwrites

## Keyboard Shortcuts

- **ENTER**: Add ROI (Box/Polygon)
- **Double-Click**: Complete Polygon
- **Q**: Deactivate selector
- **A**: Activate selector
- **Scroll**: Zoom in/out

## Features Detail

### Contrast Control
Adjust image brightness with the Contrast slider below the image. Helps visualize faint localizations.

### Channel Selection
For multi-channel data (SDmixer), select which channel to display and process.

### Pixel Size
Adjust pixel size in nanometers to correctly scale ROI selections to your data.

### Save Modes

1. **Combined**: All selected ROIs merged into single output file
2. **Separate**: Each ROI exported to individual file (_ROI1, _ROI2, etc.)

## GUI Screenshot

![ROI Selection Tool Interface](https://github.com/ngimber/SMLM_ROI-Selector/main/screenshots/gui.tif)

## Data Privacy

- Input files are **never modified** - only read
- All processing creates new files with `_selected` or `_cropped` suffix
- Original data always preserved

## Citation

If you use this tool in your research, please cite:
```
ROI Selection Tool for Microscopy
Developed by: Niclas Gimber, Charité
```

## Contact

For issues or questions: niclas.gimber@charite.de

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Technical Details

- Built with: matplotlib, numpy, pandas
- GUI Framework: tkinter (built-in)
- Platform: Windows 7+, Linux, macOS
- Data Format: CSV, TXT (tab/space-separated)

## Troubleshooting

### "Module not found" Error
```bash
pip install --upgrade matplotlib numpy pandas
```

### GUI doesn't appear
Run directly in terminal to see error messages:
```bash
python smlm_roi_selector.py
```

### Large datasets load slowly
This is normal for >100,000 localizations. Processing time depends on file size and system specs.

### ROI selection not appearing
Ensure you press **ENTER** after drawing to confirm ROI addition.

## Development

For modifications or enhancements, edit the source code directly. Key sections:
- `initialize_selector()` - Drawing mode logic
- `toggle_selector()` - ROI processing logic
- `save_data()` - Output file format

## Version History

- **v1.0** (Feb 2026): Initial release
  - Box, Polygon, Freehand drawing modes
  - SELECT/REMOVE operations
  - ThunderSTORM & SDmixer support
  - Combined/Separate save modes

