import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox,
    QRadioButton, QButtonGroup, QLabel, QGroupBox, QScrollArea
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
import pandas as pd
from shapely.geometry import LineString

class WellPlotter(QWidget):
    def __init__(self, df_wells):
        super().__init__()
        self.df_wells = df_wells
        self.initUI()

    def initUI(self):
        # Main Layout
        main_layout = QHBoxLayout()

        # Controls Layout
        controls_layout = QVBoxLayout()

        # Scroll Area for Checkboxes (optional for large number of checkboxes)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # GroupBoxes for Organization
        type_group = QGroupBox("Well Types")
        status_group = QGroupBox("Well Statuses")
        drilling_status_group = QGroupBox("Drilling Statuses")
        color_scheme_group = QGroupBox("Color Scheme")

        # Layouts for GroupBoxes
        type_layout = QVBoxLayout()
        status_layout = QVBoxLayout()
        drilling_status_layout = QVBoxLayout()
        color_scheme_layout = QVBoxLayout()

        # Creating checkboxes for each well type
        self.checkbox_type_dict = {}
        unique_types = sorted(self.df_wells['type'].unique())
        for well_type in unique_types:
            cb = QCheckBox(well_type.capitalize())
            cb.setChecked(True)  # Checked by default to show all
            cb.stateChanged.connect(self.update_plot)
            type_layout.addWidget(cb)
            self.checkbox_type_dict[well_type] = cb
        type_group.setLayout(type_layout)

        # Creating checkboxes for each well status
        self.checkbox_status_dict = {}
        unique_statuses = sorted(self.df_wells['status'].unique())
        for status in unique_statuses:
            cb = QCheckBox(status.capitalize())
            cb.setChecked(True)  # Checked by default to show all
            cb.stateChanged.connect(self.update_plot)
            status_layout.addWidget(cb)
            self.checkbox_status_dict[status] = cb
        status_group.setLayout(status_layout)

        # Creating checkboxes for each drilling status
        self.checkbox_drilling_status_dict = {}
        unique_drilling_statuses = sorted(self.df_wells['drilling_status'].unique())
        for drilling_status in unique_drilling_statuses:
            cb = QCheckBox(drilling_status.replace('_', ' ').capitalize())
            cb.setChecked(True)  # Checked by default to show all
            cb.stateChanged.connect(self.update_plot)
            drilling_status_layout.addWidget(cb)
            self.checkbox_drilling_status_dict[drilling_status] = cb
        drilling_status_group.setLayout(drilling_status_layout)

        # Creating radio buttons for color scheme
        self.radio_color_type = QRadioButton("Color by Well Type")
        self.radio_color_type.setChecked(True)  # Default selection
        self.radio_color_status = QRadioButton("Color by Well Status")
        self.radio_color_type.toggled.connect(self.update_plot)

        color_scheme_layout.addWidget(self.radio_color_type)
        color_scheme_layout.addWidget(self.radio_color_status)
        color_scheme_group.setLayout(color_scheme_layout)

        # Adding GroupBoxes to scroll layout
        scroll_layout.addWidget(type_group)
        scroll_layout.addWidget(status_group)
        scroll_layout.addWidget(drilling_status_group)
        scroll_layout.addWidget(color_scheme_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        controls_layout.addWidget(scroll)

        # Plot Layout
        plot_layout = QVBoxLayout()

        # Matplotlib Figure and Canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        plot_layout.addWidget(self.canvas)

        # Adding layouts to main layout
        main_layout.addLayout(controls_layout, 1)  # Stretch factor 1
        main_layout.addLayout(plot_layout, 3)      # Stretch factor 3

        self.setLayout(main_layout)
        self.setWindowTitle('Well Plotter with Advanced Controls')
        self.show()

        # Initialize Plotting Variables
        self.init_plot()

    def init_plot(self):
        # Define line styles based on drilling status
        self.drilling_styles = {
            'drilled': {'linestyle': '-'},
            'planned': {'linestyle': '--'},
            'currently_drilling': {'linestyle': ':'}
        }

        # Define color mapping based on well type and well status
        self.type_color_map = {
            'oil': 'red',
            'gas': 'green',
            'water': 'blue',
            'injection': 'purple'
            # Add more types and colors as needed
        }

        self.status_color_map = {
            'producing': 'cyan',
            'shut in': 'magenta',
            'injecting': 'orange'
            # Add more statuses and colors as needed
        }

        # Initialize LineCollections for each drilling status
        self.drilling_collections = {}
        for drilling_status, style in self.drilling_styles.items():
            lc = LineCollection([], linestyles=style['linestyle'], linewidths=1.5, zorder=2)
            self.drilling_collections[drilling_status] = lc
            self.ax.add_collection(lc)

        # Prepare segments and their properties
        self.prepare_segments()

        # Adjust plot limits
        self.ax.autoscale()
        self.ax.set_aspect('equal', 'datalim')

        # Create Legend
        self.create_legend()

        self.canvas.draw()

    def prepare_segments(self):
        # Group data by well_id and drilling_status to form LineStrings
        grouped = self.df_wells.sort_values('sequence').groupby(['well_id', 'drilling_status'])

        # Initialize a dictionary to hold segments and their properties per drilling status
        self.segments_per_drilling_status = {status: [] for status in self.drilling_styles.keys()}
        self.colors_per_drilling_status = {status: [] for status in self.drilling_styles.keys()}

        # Store mappings from (well_id, drilling_status) to (type, status)
        self.segment_properties = {status: [] for status in self.drilling_styles.keys()}

        for (well_id, drilling_status), group in grouped:
            coords = list(zip(group['x'], group['y']))
            if len(coords) < 2:
                continue  # Need at least two points to form a line
            line = LineString(coords)
            segment = list(line.coords)
            self.segments_per_drilling_status[drilling_status].append(segment)

            # Assuming all points in a group have the same type and status
            well_type = group['type'].iloc[0]
            well_status = group['status'].iloc[0]
            self.segment_properties[drilling_status].append({
                'type': well_type,
                'status': well_status
            })

        # Assign segments and default colors to each LineCollection
        for drilling_status, lc in self.drilling_collections.items():
            lc.set_segments(self.segments_per_drilling_status[drilling_status])
            # Default color: based on well type or well status
            # Initially, color by well type
            colors = [
                self.type_color_map.get(prop['type'], 'black')
                for prop in self.segment_properties[drilling_status]
            ]
            lc.set_color(colors)
            # Store all properties for later filtering
            lc.segment_props = self.segment_properties[drilling_status]

    def create_legend(self):
        # Create custom legend handles
        from matplotlib.lines import Line2D

        legend_elements = []

        # Line styles for drilling statuses
        for drilling_status, style in self.drilling_styles.items():
            legend_elements.append(Line2D([0], [0], color='black',
                                          linestyle=style['linestyle'],
                                          label=drilling_status.replace('_', ' ').capitalize()))

        # Color indicators for well types
        for well_type, color in self.type_color_map.items():
            legend_elements.append(Line2D([0], [0], color=color, lw=2, label=well_type.capitalize()))

        # Color indicators for well statuses (only if coloring by status)
        for well_status, color in self.status_color_map.items():
            legend_elements.append(Line2D([0], [0], color=color, lw=2, label=well_status.capitalize()))

        self.ax.legend(handles=legend_elements, loc='upper right')

    def update_plot(self):
        # Determine current color scheme
        color_by_type = self.radio_color_type.isChecked()

        # Get selected well types
        selected_types = [
            well_type for well_type, cb in self.checkbox_type_dict.items() if cb.isChecked()
        ]

        # Get selected well statuses
        selected_statuses = [
            status for status, cb in self.checkbox_status_dict.items() if cb.isChecked()
        ]

        # Get selected drilling statuses
        selected_drilling_statuses = [
            drilling_status for drilling_status, cb in self.checkbox_drilling_status_dict.items() if cb.isChecked()
        ]

        # Update each LineCollection based on drilling status
        for drilling_status, lc in self.drilling_collections.items():
            # Visibility based on drilling status checkboxes
            lc.set_visible(drilling_status in selected_drilling_statuses)

            # Prepare new segments and colors
            new_segments = []
            new_colors = []

            for segment, props in zip(self.segments_per_drilling_status[drilling_status], lc.segment_props):
                if (props['type'] in selected_types) and (props['status'] in selected_statuses):
                    new_segments.append(segment)
                    if color_by_type:
                        color = self.type_color_map.get(props['type'], 'black')
                    else:
                        color = self.status_color_map.get(props['status'], 'black')
                    new_colors.append(color)

            # Update LineCollection segments and colors
            lc.set_segments(new_segments)
            lc.set_color(new_colors)

        self.canvas.draw()

    def plot_wells(self):
        # Define line styles based on drilling status
        self.drilling_styles = {
            'drilled': {'linestyle': '-'},
            'planned': {'linestyle': '--'},
            'currently_drilling': {'linestyle': ':'}
        }

        # Define color mapping based on well type and well status
        self.type_color_map = {
            'oil': 'red',
            'gas': 'green',
            'water': 'blue',
            'injection': 'purple'
            # Add more types and colors as needed
        }

        self.status_color_map = {
            'producing': 'cyan',
            'shut in': 'magenta',
            'injecting': 'orange'
            # Add more statuses and colors as needed
        }

        # Initialize LineCollections for each drilling status
        self.drilling_collections = {}
        for drilling_status, style in self.drilling_styles.items():
            lc = LineCollection([], linestyles=style['linestyle'], linewidths=1.5, zorder=2)
            self.drilling_collections[drilling_status] = lc
            self.ax.add_collection(lc)

        # Group data by well_id and drilling_status to form LineStrings
        grouped = self.df_wells.sort_values('sequence').groupby(['well_id', 'drilling_status'])

        # Initialize a dictionary to hold segments and their properties per drilling status
        self.segments_per_drilling_status = {status: [] for status in self.drilling_styles.keys()}
        self.colors_per_drilling_status = {status: [] for status in self.drilling_styles.keys()}

        # Store mappings from (well_id, drilling_status) to (type, status)
        self.segment_properties = {status: [] for status in self.drilling_styles.keys()}

        for (well_id, drilling_status), group in grouped:
            coords = list(zip(group['x'], group['y']))
            if len(coords) < 2:
                continue  # Need at least two points to form a line
            line = LineString(coords)
            segment = list(line.coords)
            self.segments_per_drilling_status[drilling_status].append(segment)

            # Assuming all points in a group have the same type and status
            well_type = group['type'].iloc[0]
            well_status = group['status'].iloc[0]
            self.segment_properties[drilling_status].append({
                'type': well_type,
                'status': well_status
            })

        # Assign segments and default colors to each LineCollection
        for drilling_status, lc in self.drilling_collections.items():
            lc.set_segments(self.segments_per_drilling_status[drilling_status])
            # Default color: based on well type
            colors = [
                self.type_color_map.get(prop['type'], 'black')
                for prop in self.segment_properties[drilling_status]
            ]
            lc.set_color(colors)
            # Store all properties for later filtering
            lc.segment_props = self.segment_properties[drilling_status]

        # Adjust plot limits
        self.ax.autoscale()
        self.ax.set_aspect('equal', 'datalim')

        # Create Legend
        self.create_legend()

if __name__ == '__main__':
    # Sample DataFrame
    data = {
        'well_id': ['555555', '555555', '555555', '555555',
                    '666666', '666666', '666666', '666666',
                    '777777', '777777', '777777', '777777'],
        'type': ['oil', 'oil', 'gas', 'gas',
                'water', 'water', 'oil', 'oil',
                'injection', 'injection', 'water', 'water'],
        'status': ['producing', 'producing', 'shut in', 'shut in',
                'injecting', 'injecting', 'producing', 'shut in',
                'injecting', 'shut in', 'producing', 'shut in'],
        'drilling_status': ['planned', 'drilled', 'currently_drilling', 'drilled',
                            'planned', 'currently_drilling', 'drilled', 'planned',
                            'currently_drilling', 'drilled', 'planned', 'currently_drilling'],
        'sequence': [1, 2, 1, 2,
                    1, 2, 1, 2,
                    1, 2, 1, 2],
        'x': [0, 1, 2, 3,
              4, 5, 6, 7,
              8, 9, 10, 11],
        'y': [0, 1, 0, 1,
              0, 1, 0, 1,
              0, 1, 0, 1]
    }

    df_wells = pd.DataFrame(data)

    app = QApplication(sys.argv)
    ex = WellPlotter(df_wells)
    sys.exit(app.exec_())
