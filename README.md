# OGMBoardProject
 OGM Board Data
# Well Visualizer

## Description
Well Visualizer is a sophisticated Python application for visualizing and analyzing well data, particularly focused on oil and gas wells. It provides an interactive interface for displaying well locations, trajectories, and associated data in both 2D and 3D views.

## Features
- Interactive well visualization in 2D and 3D
- Well trajectory plotting (planned, currently drilling, and drilled wells)
- Section and plat visualization
- Field boundary visualization
- Well status filtering (oil, gas, water disposal, dry holes, etc.)
- Operator-based filtering
- Production data visualization
- Board matters integration
- Interactive zooming and panning capabilities
- Mineral ownership visualization
- Custom styling for different well types and statuses

## Dependencies
### Core Data/Scientific
- NumPy
- Pandas
- GeoPandas
- UTM

### GUI
- PyQt5

### Visualization
- Matplotlib

### Geospatial
- Shapely

### Database
- SQLite3
- SQLAlchemy

### Other
- regex

## Installation
(Add installation instructions here based on your project's setup requirements)

## Project Structure
- `WellVisualizerMain.py`: Main application file containing the core visualization logic
- `WellVisualizerBoardMatters.py`: Handles board matters visualization
- `WellVisualizationUI.py`: Contains the UI definition
- `ModuleAgnostic.py`: Contains shared utilities and functions

## Key Components

### Custom Delegates
- `MultiBoldRowDelegate`: Handles bold formatting for specific rows in Qt views
- `BoldDelegate`: Applies bold formatting to specific values in Qt views

### Main Application Class
`wellVisualizationProcess`: The primary class that:
- Manages the application's main window
- Handles well data visualization
- Processes user interactions
- Manages various data models and views
- Controls visualization layers and styling

## Features Details

### Well Types Supported
- Oil Wells
- Gas Wells
- Water Disposal Wells
- Dry Holes
- Injection Wells
- Other Well Types

### Well Status Types
- Producing
- Shut In
- PA (Plugged and Abandoned)
- Drilling
- Miscellaneous

### Visualization Capabilities
- Section/Plat Boundaries
- Well Trajectories
- Field Boundaries
- Ownership Information
- Production Data
- Board Matter Highlights

## Authors
- Colton Goodrich

## Last Updated
August 31, 2024

---
Note: This is a complex visualization tool specifically designed for well data analysis and requires specific data formats and database structures to function properly.