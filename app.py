import streamlit as st
import pandas as pd
import requests
import os
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from dotenv import load_dotenv
from streamlit_plotly_events import plotly_events

# Load environment variables
load_dotenv()

def save_metrics_to_file(metrics, metrics_names, metrics_groups=None):
    """Save metrics to a local JSON file for persistence"""
    try:
        data = {
            'saved_metrics': metrics,
            'saved_metrics_names': metrics_names,
            'saved_metrics_groups': metrics_groups or {}
        }
        with open('saved_metrics.json', 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        st.error(f"Could not save metrics: {e}")

def load_metrics_from_file():
    """Load metrics from local JSON file"""
    try:
        if os.path.exists('saved_metrics.json'):
            with open('saved_metrics.json', 'r') as f:
                data = json.load(f)
                return (
                    data.get('saved_metrics', []), 
                    data.get('saved_metrics_names', {}),
                    data.get('saved_metrics_groups', {})
                )
        return [], {}, {}
    except Exception as e:
        st.error(f"Could not load saved metrics: {e}")
        return [], {}, {}
    
    # Common CSS for spacing (removed complex button styling)
    common_css = """
    <style>
    /* Reduce top padding and margins */
    .main > div {
        padding-top: 2rem !important;
    }
    .sidebar .sidebar-content {
        padding-top: 0.5rem !important;
    }
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* Further reduce sidebar spacing */
    .css-1d391kg {
        padding-top: 0.5rem !important;
    }
    .css-1y4p8pa {
        padding-top: 0.25rem !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem !important;
    }
    </style>
    """
    
    # Combine theme and common CSS
    full_css = theme_css + common_css
    st.markdown(full_css, unsafe_allow_html=True)

class FredAPI:
    """Class to handle FRED API interactions"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
    
    def get_series_data(self, series_id, start_date=None, end_date=None):
        """
        Fetch time series data from FRED API
        
        Args:
            series_id (str): FRED series identifier
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            pandas.DataFrame: Time series data
        """
        url = f"{self.base_url}/series/observations"
        
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json'
        }
        
        if start_date:
            params['observation_start'] = start_date
        if end_date:
            params['observation_end'] = end_date
            
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'observations' in data:
                observations = data['observations']
                df = pd.DataFrame(observations)
                
                if not df.empty:
                    # Convert date column and handle missing values
                    df['date'] = pd.to_datetime(df['date'])
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    
                    # Remove rows with missing values (marked as '.' in FRED)
                    df = df.dropna(subset=['value'])
                    
                    # Sort by date
                    df = df.sort_values('date')
                    df.reset_index(drop=True, inplace=True)
                    
                return df
            else:
                return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"Error processing data: {e}")
            return pd.DataFrame()
    
    def get_series_info(self, series_id):
        """
        Get metadata about a FRED series
        
        Args:
            series_id (str): FRED series identifier
            
        Returns:
            dict: Series metadata
        """
        url = f"{self.base_url}/series"
        
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'seriess' in data and len(data['seriess']) > 0:
                return data['seriess'][0]
            else:
                return {}
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching series info: {e}")
            return {}
        except Exception as e:
            st.error(f"Error processing series info: {e}")
            return {}

@st.dialog("🎨 Line Formatting Options")
def format_line_dialog():
    """Modal dialog for line formatting options"""
    
    # Create tabs for different formatting options
    tab1, tab2 = st.tabs(["🖍️ Drawing Lines", "📈 Data Line"])
    
    with tab1:
        st.subheader("Drawing Line Color")
        
        # Color picker widget
        new_drawing_color = st.color_picker(
            "Choose drawing line color:",
            value=st.session_state.line_color,
            key="drawing_color_picker"
        )
        
        # Update color if changed (but don't rerun immediately)
        if new_drawing_color != st.session_state.line_color:
            st.session_state.line_color = new_drawing_color
        
        st.subheader("Line Style")
        line_styles = {
            "Solid": "solid",
            "Dashed": "dash", 
            "Dotted": "dot",
            "Dash-Dot": "dashdot",
            "Long Dash": "longdash",
            "Long Dash-Dot": "longdashdot"
        }
        
        selected_style = st.selectbox(
            "Line Type:",
            options=list(line_styles.keys()),
            index=list(line_styles.values()).index(st.session_state.line_type),
            key="modal_line_style_select"
        )
        st.session_state.line_type = line_styles[selected_style]
        
        st.subheader("Line Thickness")
        thickness = st.slider(
            "Thickness (px):",
            min_value=1,
            max_value=10,
            value=st.session_state.line_thickness,
            step=1,
            key="modal_line_thickness_slider"
        )
        st.session_state.line_thickness = thickness
    
    with tab2:
        st.subheader("Data Line Color")
        
        # Color picker widget
        new_data_color = st.color_picker(
            "Choose data line color:",
            value=st.session_state.data_line_color,
            key="data_color_picker"
        )
        
        # Update color if changed (but don't rerun immediately)
        if new_data_color != st.session_state.data_line_color:
            st.session_state.data_line_color = new_data_color
        
    # Close button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Apply Changes", type="primary"):
            st.rerun()
    with col2:
        if st.button("❌ Close"):
            pass  # Just closes the dialog without rerunning

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="FRED Economic Data Explorer",
        page_icon="📊",
        layout="wide"
    )
    
    # Title and description
    st.markdown("# 📊 FRED Economic Data Explorer")
    st.markdown("Fetch and explore economic data from the Federal Reserve Economic Data (FRED) database.")
    
    # Check for API key
    api_key = None
    
    # Try Streamlit secrets first (for deployment)
    try:
        api_key = st.secrets["FRED_API_KEY"]
    except:
        # Fall back to environment variable (for local development)
        api_key = os.getenv('FRED_API_KEY')
    
    if not api_key or api_key == 'your_fred_api_key_here':
        st.error("⚠️ Please set your FRED API key")
        st.markdown("""
        **For local development:**
        1. Get a free API key from [FRED](https://research.stlouisfed.org/docs/api/api_key.html)
        2. Add it to the `.env` file: `FRED_API_KEY=your_actual_key_here`
        3. Restart the application
        
        **For Streamlit Cloud:**
        1. Add your API key in the app's Secrets management
        2. Format: `FRED_API_KEY = "your_actual_key_here"`
        """)
        return
    
    # Initialize FRED API client
    fred_api = FredAPI(api_key)
    
    # Sidebar for inputs
    st.sidebar.markdown("### Data Selection")
    
    # Series ID input
    if 'selected_series' not in st.session_state:
        st.session_state.selected_series = "GDP"
    
    series_id = st.sidebar.text_input(
        "FRED Series ID",
        value=st.session_state.selected_series,
        help="Enter a FRED series identifier (e.g., GDP, UNRATE, CPIAUCSL)"
    ).strip().upper()
    
    # Update session state if user manually changes the input
    if series_id != st.session_state.selected_series:
        st.session_state.selected_series = series_id
    
    # Date range selection
    st.sidebar.markdown("**Date Range**")
    
    # Quick date range dropdown
    date_range_options = {
        "All Time": "all",
        "Last 5 Years": "5y",
        "Last 1 Year": "1y", 
        "Year-to-Date": "ytd",
        "Last 6 Months": "6m",
        "Last 3 Months": "3m",
        "Custom Range": "custom"
    }
    
    selected_range = st.sidebar.selectbox(
        "Quick Select:",
        options=list(date_range_options.keys()),
        index=0,  # Default to "All Time"
        help="Choose a predefined date range or custom"
    )
    
    # Update session state based on selection
    st.session_state.date_range = date_range_options[selected_range]
    
    # Calculate date ranges based on selection
    end_date = datetime.now()
    
    if st.session_state.date_range == "all":
        start_date = None
        end_date = None
    elif st.session_state.date_range == "5y":
        start_date = end_date - timedelta(days=365*5)
    elif st.session_state.date_range == "1y":
        start_date = end_date - timedelta(days=365)
    elif st.session_state.date_range == "ytd":
        start_date = datetime(end_date.year, 1, 1)
    elif st.session_state.date_range == "6m":
        start_date = end_date - timedelta(days=180)
    elif st.session_state.date_range == "3m":
        start_date = end_date - timedelta(days=90)
    elif st.session_state.date_range == "custom":
        start_date = None
        end_date = None
    else:
        start_date = None
        end_date = None
    
    # Custom date range inputs - only show when "Custom Range" is selected
    if st.session_state.date_range == "custom":
        st.sidebar.markdown("**Custom Date Range:**")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            custom_start_date = st.date_input(
                "Start Date",
                value=None,
                help="Enter custom start date"
            )
        
        with col2:
            custom_end_date = st.date_input(
                "End Date", 
                value=None,
                help="Enter custom end date"
            )
        
        # Use the custom dates if provided
        if custom_start_date is not None:
            start_date = datetime.combine(custom_start_date, datetime.min.time())
        if custom_end_date is not None:
            end_date = datetime.combine(custom_end_date, datetime.min.time())
    
    # Convert dates to string format for API call
    start_date_str = start_date.strftime('%Y-%m-%d') if start_date else None
    end_date_str = end_date.strftime('%Y-%m-%d') if end_date else None
    
    # Fetch data button - above saved metrics
    if st.sidebar.button("Fetch Data", type="primary") or series_id:
        fetch_data_requested = True
    else:
        fetch_data_requested = False
    
    # Saved Metrics section with inline pencil
    col1, col2 = st.sidebar.columns([4, 1])
    with col1:
        st.markdown("**Saved Metrics**")
    with col2:
        # Initialize edit mode state
        if 'edit_mode' not in st.session_state:
            st.session_state.edit_mode = False
        
        # Pencil button with emoji inside
        if st.button("✏️", key="edit_toggle", help="Toggle edit mode"):
            st.session_state.edit_mode = not st.session_state.edit_mode
            st.rerun()
    
    edit_mode = st.session_state.edit_mode
    
    # Initialize saved metrics in session state
    if 'saved_metrics' not in st.session_state:
        # Load from file on first run
        saved_metrics, saved_metrics_names, saved_metrics_groups = load_metrics_from_file()
        st.session_state.saved_metrics = saved_metrics
        st.session_state.saved_metrics_names = saved_metrics_names
        st.session_state.saved_metrics_groups = saved_metrics_groups
    
    # Initialize saved metrics names cache if not loaded from file
    if 'saved_metrics_names' not in st.session_state:
        st.session_state.saved_metrics_names = {}
    
    # Initialize saved metrics groups if not exists
    if 'saved_metrics_groups' not in st.session_state:
        st.session_state.saved_metrics_groups = {}
    
    # Add new metric button
    if st.sidebar.button("➕ Add New Metric"):
        st.session_state.show_add_metric = True
    
    # Modal-like popup for adding new metric
    if 'show_add_metric' in st.session_state and st.session_state.show_add_metric:
        with st.sidebar.container():
            st.markdown("**Add New Metric:**")
            new_metric = st.text_input(
                "FRED Series ID",
                placeholder="e.g., UNRATE, GDP, CPIAUCSL",
                help="Enter a valid FRED series identifier"
            )
            
            # Group selection
            existing_groups = list(set(st.session_state.saved_metrics_groups.values()))
            existing_groups.sort()
            
            group_input_type = st.radio(
                "Group",
                ["Select existing", "Create new"],
                horizontal=True,
                key="group_input_type"
            )
            
            if group_input_type == "Select existing" and existing_groups:
                selected_group = st.selectbox(
                    "Choose group",
                    ["None"] + existing_groups,
                    key="selected_existing_group"
                )
                metric_group = None if selected_group == "None" else selected_group
            elif group_input_type == "Create new":
                metric_group = st.text_input(
                    "New group name",
                    placeholder="e.g., Most Used, Demand Metrics, Capacity Metrics",
                    key="new_group_name"
                )
                if not metric_group.strip():
                    metric_group = None
            else:
                metric_group = None
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save", key="save_metric"):
                    if new_metric.strip():
                        metric_upper = new_metric.strip().upper()
                        if metric_upper not in st.session_state.saved_metrics:
                            st.session_state.saved_metrics.append(metric_upper)
                            # Save group assignment
                            if metric_group and metric_group.strip():
                                st.session_state.saved_metrics_groups[metric_upper] = metric_group.strip()
                            # Fetch the full name for this metric
                            try:
                                temp_fred = FredAPI(api_key)
                                series_info = temp_fred.get_series_info(metric_upper)
                                if series_info and series_info.get('title'):
                                    st.session_state.saved_metrics_names[metric_upper] = series_info['title']
                                else:
                                    st.session_state.saved_metrics_names[metric_upper] = metric_upper
                            except:
                                st.session_state.saved_metrics_names[metric_upper] = metric_upper
                            
                            # Save to file for persistence
                            save_metrics_to_file(
                                st.session_state.saved_metrics, 
                                st.session_state.saved_metrics_names,
                                st.session_state.saved_metrics_groups
                            )
                            st.success(f"Added {metric_upper}!")
                        else:
                            st.warning(f"{metric_upper} already saved!")
                        st.session_state.show_add_metric = False
                        st.rerun()
                    else:
                        st.error("Please enter a metric ID")
            
            with col2:
                if st.button("Cancel", key="cancel_metric"):
                    st.session_state.show_add_metric = False
                    st.rerun()
    
    # Display saved metrics as buttons
    if st.session_state.saved_metrics:
        st.sidebar.markdown("**Quick Access:**")
        
        # Group filter dropdown
        all_groups = ["All"] + sorted(list(set(st.session_state.saved_metrics_groups.values())))
        if len(all_groups) > 1:  # Only show filter if there are groups
            selected_filter = st.sidebar.selectbox(
                "Filter by group:",
                all_groups,
                key="group_filter"
            )
        else:
            selected_filter = "All"
        
        # Filter metrics based on selected group
        if selected_filter == "All":
            filtered_metrics = st.session_state.saved_metrics
        else:
            filtered_metrics = [
                metric for metric in st.session_state.saved_metrics
                if st.session_state.saved_metrics_groups.get(metric) == selected_filter
            ]
        
        for i, metric in enumerate(filtered_metrics):
            if edit_mode:
                # Edit mode: show X button inline with metric name
                # Get full name or use metric ID as fallback
                display_name = st.session_state.saved_metrics_names.get(metric, metric)
                group_name = st.session_state.saved_metrics_groups.get(metric)
                if group_name:
                    button_text = f"{display_name} [{group_name}]"
                    help_text = f"Load {metric} data (Group: {group_name})"
                else:
                    button_text = display_name
                    help_text = f"Load {metric} data"
                
                # Create two buttons side by side
                col1, col2 = st.sidebar.columns([1, 4])
                with col1:
                    if st.button("❌", key=f"delete_{metric}_{i}", help="Remove this metric"):
                        st.session_state.saved_metrics.remove(metric)
                        # Remove from groups as well
                        if metric in st.session_state.saved_metrics_groups:
                            del st.session_state.saved_metrics_groups[metric]
                        if metric in st.session_state.saved_metrics_names:
                            del st.session_state.saved_metrics_names[metric]
                        # Save to file for persistence
                        save_metrics_to_file(
                            st.session_state.saved_metrics, 
                            st.session_state.saved_metrics_names,
                            st.session_state.saved_metrics_groups
                        )
                        st.rerun()
                with col2:
                    if st.button(button_text, key=f"metric_{metric}_{i}", help=help_text):
                        st.session_state.selected_series = metric
                        st.rerun()
            else:
                # Normal mode: just show the button
                display_name = st.session_state.saved_metrics_names.get(metric, metric)
                group_name = st.session_state.saved_metrics_groups.get(metric)
                if group_name:
                    button_text = f"{display_name} [{group_name}]"
                    help_text = f"Load {metric} data (Group: {group_name})"
                else:
                    button_text = display_name
                    help_text = f"Load {metric} data"
                
                if st.sidebar.button(button_text, key=f"metric_{metric}_{i}", help=help_text):
                    st.session_state.selected_series = metric
                    st.rerun()
    else:
        st.sidebar.info("No saved metrics yet. Add some for quick access!")
    
    # Process data fetching - show chart whenever there's a series_id
    if series_id:
        with st.spinner(f"Fetching data for {series_id}..."):
            # Get series information
            series_info = fred_api.get_series_info(series_id)
            
            # Get series data
            df = fred_api.get_series_data(series_id, start_date_str, end_date_str)
            
            if not df.empty:
                # Display series information
                if series_info:
                    st.subheader(f"📈 {series_info.get('title', series_id)}")
                
                # Chart controls
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    enable_drawing = st.checkbox("✏️ Enable Drawing Mode", help="Check to draw trendlines on the chart")
                    light_mode_chart = st.checkbox("☀️ Light Mode Chart", help="Toggle light mode for the chart only")
                with col2:
                    # Show format line button only when drawing mode is enabled
                    if enable_drawing:
                        # Initialize line formatting options in session state
                        if 'line_color' not in st.session_state:
                            st.session_state.line_color = "#ff0000"  # Default red
                        if 'line_type' not in st.session_state:
                            st.session_state.line_type = "solid"
                        if 'line_thickness' not in st.session_state:
                            st.session_state.line_thickness = 2
                        if 'data_line_color' not in st.session_state:
                            st.session_state.data_line_color = "#1f77b4"  # Default blue
                        if 'saved_shapes' not in st.session_state:
                            st.session_state.saved_shapes = []  # Store drawn shapes
                        
                        # Format Line button with popup
                        if st.button("🎨 Format Line", help="Customize line appearance"):
                            format_line_dialog()
                    
                    clear_lines = st.button("🗑️ Clear All Lines", help="Remove all drawn trendlines")
                
                # Initialize chart refresh state
                if 'chart_key' not in st.session_state:
                    st.session_state.chart_key = 0
                
                # Handle clear all lines
                if clear_lines:
                    st.session_state.chart_key += 1
                    st.session_state.saved_shapes = []  # Clear saved shapes
                    st.rerun()
                
                # Initialize trendlines in session state
                if 'trendlines' not in st.session_state:
                    st.session_state.trendlines = []
                
                # Create the interactive chart
                fig = go.Figure()
                
                # Add the main data line
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['value'],
                    mode='lines+markers',
                    name='Data',
                    line=dict(color=st.session_state.get('data_line_color', '#1f77b4'), width=2),
                    marker=dict(size=4, color=st.session_state.get('data_line_color', '#1f77b4')),
                    hovertemplate='<b>Date:</b> %{x}<br><b>Value:</b> %{y:.2f}<extra></extra>'
                ))
                
                # Configure chart layout
                fig.update_layout(
                    title={
                        'text': f"{series_info.get('title', series_id)}",
                        'x': 0.5,  # Center horizontally
                        'xanchor': 'center',
                        'font': {
                            'size': 18,  # Larger font size
                            'color': 'black' if light_mode_chart else 'white'
                        }
                    },
                    xaxis_title="Date",
                    yaxis_title=f"Value ({series_info.get('units', '')})",
                    hovermode='x unified',
                    showlegend=True,
                    height=500,
                    margin=dict(l=0, r=0, t=60, b=0),  # Increased top margin for larger title
                    # Clear annotations when chart key changes
                    annotations=[] if clear_lines else None,
                    # Restore saved shapes unless clearing
                    shapes=[] if clear_lines else st.session_state.get('saved_shapes', []),
                    # Dynamic chart theme based on light mode toggle
                    paper_bgcolor='white' if light_mode_chart else '#0e1117',
                    plot_bgcolor='white' if light_mode_chart else '#0e1117',
                    font=dict(
                        color='black' if light_mode_chart else 'white'
                    ),
                    xaxis=dict(
                        gridcolor='#dee2e6' if light_mode_chart else '#2f3037',
                        zerolinecolor='#dee2e6' if light_mode_chart else '#2f3037',
                        tickfont=dict(color='black' if light_mode_chart else 'white'),
                        title=dict(
                            font=dict(color='black' if light_mode_chart else 'white')
                        )
                    ),
                    yaxis=dict(
                        gridcolor='#dee2e6' if light_mode_chart else '#2f3037',
                        zerolinecolor='#dee2e6' if light_mode_chart else '#2f3037',
                        tickfont=dict(color='black' if light_mode_chart else 'white'),
                        title=dict(
                            font=dict(color='black' if light_mode_chart else 'white')
                        )
                    ),
                    legend=dict(
                        font=dict(color='black' if light_mode_chart else 'white')
                    ),
                    # Set default formatting for new drawing shapes
                    newshape=dict(
                        line_color=st.session_state.get('line_color', '#ff0000'),
                        line_width=st.session_state.get('line_thickness', 2),
                        line_dash=st.session_state.get('line_type', 'solid')
                    ) if enable_drawing else None
                )
                
                # Enable drawing tools if requested
                config = {
                    'displayModeBar': True,
                    'modeBarButtonsToAdd': [] if not enable_drawing else [
                        'drawline',
                        'drawopenpath',
                        'drawclosedpath',
                        'drawcircle',
                        'drawrect',
                        'eraseshape'
                    ],
                    'displaylogo': False,
                    'toImageButtonOptions': {
                        'format': 'png',
                        'filename': f'{series_id}_chart',
                        'height': 500,
                        'width': 800,
                        'scale': 1
                    },
                    # Set default drawing color
                    'modeBarButtonsToRemove': [],
                    'plotGlPixelRatio': 1
                }
                
                # Display the chart with stable key (only changes when clearing lines or new data)
                chart_placeholder = st.plotly_chart(
                    fig, 
                    use_container_width=True, 
                    config=config,
                    key=f"chart_{series_id}_{st.session_state.chart_key}"
                )
                    
                
                # Instructions for drawing
                if enable_drawing:
                    # Get current line style name for display
                    style_names = {
                        "solid": "Solid",
                        "dash": "Dashed", 
                        "dot": "Dotted",
                        "dashdot": "Dash-Dot",
                        "longdash": "Long Dash",
                        "longdashdot": "Long Dash-Dot"
                    }
                    current_style = style_names.get(st.session_state.get('line_type', 'solid'), 'Solid')
                    
                    st.info(f"""
                    📝 **Drawing Instructions:**
                    - Use the drawing tools in the chart toolbar (top right)
                    - Click the line tool to draw trendlines
                    - **Current Format:** {st.session_state.get('line_color', '#ff0000')} | {current_style} | {st.session_state.get('line_thickness', 2)}px
                    - Use 'Format Line' to customize appearance
                    - Click the eraser tool to remove drawings
                    - Use 'Clear All Lines' button to remove all trendlines at once
                    """)
                else:
                    st.info("💡 **Tip:** Enable drawing mode to add trendlines and annotations to your chart!")
                
                # Series notes and metadata below chart
                if series_info:
                    with st.expander("📋 Series Information & Notes"):
                        # Series metadata in columns
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"**Series ID:** {series_id}")
                        with col2:
                            st.markdown(f"**Frequency:** {series_info.get('frequency', 'N/A')}")
                            with col3:
                                st.markdown(f"**Units:** {series_info.get('units', 'N/A')}")
                            
                            # Series notes
                            if series_info.get('notes'):
                                st.markdown("**Notes:**")
                                st.write(series_info['notes'])
                            else:
                                st.markdown("*No additional notes available for this series.*")
                    
                    # Chart statistics
                    with st.expander("📊 Chart Statistics"):
                        data_stats = df['value'].describe()
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Minimum", f"{data_stats['min']:.2f}")
                        with col2:
                            st.metric("Maximum", f"{data_stats['max']:.2f}")
                        with col3:
                            st.metric("Standard Deviation", f"{data_stats['std']:.2f}")
                        with col4:
                            st.metric("Median", f"{data_stats['50%']:.2f}")
                    
                    # Display data table as expandable section
                    with st.expander("📋 Data Table"):
                        # Format the dataframe for display
                        display_df = df[['date', 'value']].copy()
                        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                        display_df = display_df.rename(columns={'date': 'Date', 'value': 'Value'})
                        
                        # Show recent data first
                        display_df = display_df.sort_values('Date', ascending=False)
                        
                        st.dataframe(
                            display_df,
                            width='stretch',
                            hide_index=True
                        )
                        
                        # Download button
                        csv = display_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Data as CSV",
                            data=csv,
                            file_name=f"{series_id}_data.csv",
                            mime="text/csv"
                        )
                    
                    # Summary Table for all saved metrics
                    st.subheader("📊 Summary Table")
                    
                    if st.session_state.saved_metrics:
                        # Toggle for percentage vs absolute changes
                        use_percentage = st.checkbox("Show percentage changes", value=True, help="Toggle between percentage and absolute changes")
                        
                        # Create summary data
                        summary_data = []
                        
                        for metric in st.session_state.saved_metrics:
                            try:
                                # Get metric data
                                metric_df = fred_api.get_series_data(metric)
                                metric_info = fred_api.get_series_info(metric)
                                
                                if not metric_df.empty and len(metric_df) >= 2:
                                    # Get metric name
                                    metric_name = st.session_state.saved_metrics_names.get(metric, metric)
                                    
                                    # Get frequency and units
                                    frequency = metric_info.get('frequency', 'N/A')
                                    units = metric_info.get('units', 'N/A')
                                    
                                    # Sort by date to ensure proper ordering
                                    metric_df = metric_df.sort_values('date')
                                    
                                    # Get current value and latest date
                                    latest_value = metric_df.iloc[-1]['value']
                                    latest_date = metric_df.iloc[-1]['date'].strftime('%Y-%m-%d')
                                    
                                    # Sequential change (latest vs previous)
                                    previous_value = metric_df.iloc[-2]['value']
                                    
                                    if use_percentage and previous_value != 0:
                                        sequential_change = ((latest_value - previous_value) / previous_value) * 100
                                        sequential_format = f"{sequential_change:.2f}%"
                                    else:
                                        sequential_change = latest_value - previous_value
                                        sequential_format = f"{sequential_change:.2f}"
                                    
                                    # YTD change (latest vs earliest this year)
                                    current_year = datetime.now().year
                                    ytd_start = datetime(current_year, 1, 1)
                                    
                                    # Find closest reading to Jan 1st or after
                                    ytd_df = metric_df[metric_df['date'] >= ytd_start]
                                    if not ytd_df.empty:
                                        ytd_start_value = ytd_df.iloc[0]['value']
                                        
                                        if use_percentage and ytd_start_value != 0:
                                            ytd_change = ((latest_value - ytd_start_value) / ytd_start_value) * 100
                                            ytd_format = f"{ytd_change:.2f}%"
                                        else:
                                            ytd_change = latest_value - ytd_start_value
                                            ytd_format = f"{ytd_change:.2f}"
                                    else:
                                        ytd_format = "N/A"
                                    
                                    summary_data.append({
                                        'Metric Name': metric_name,
                                        'Current Value': f"{latest_value:.2f}",
                                        'Latest Date': latest_date,
                                        'Units': units,
                                        'Frequency': frequency,
                                        'Sequential Change': sequential_format,
                                        'YTD Change': ytd_format
                                    })
                                else:
                                    # Handle case with insufficient data
                                    metric_name = st.session_state.saved_metrics_names.get(metric, metric)
                                    frequency = metric_info.get('frequency', 'N/A') if metric_info else 'N/A'
                                    units = metric_info.get('units', 'N/A') if metric_info else 'N/A'
                                    
                                    # Try to get at least the current value if we have any data
                                    if not metric_df.empty:
                                        latest_value = metric_df.iloc[-1]['value']
                                        latest_date = metric_df.iloc[-1]['date'].strftime('%Y-%m-%d')
                                        current_value = f"{latest_value:.2f}"
                                    else:
                                        current_value = 'N/A'
                                        latest_date = 'N/A'
                                    
                                    summary_data.append({
                                        'Metric Name': metric_name,
                                        'Current Value': current_value,
                                        'Latest Date': latest_date,
                                        'Units': units,
                                        'Frequency': frequency,
                                        'Sequential Change': 'N/A',
                                        'YTD Change': 'N/A'
                                    })
                                    
                            except Exception as e:
                                # Handle any errors gracefully
                                metric_name = st.session_state.saved_metrics_names.get(metric, metric)
                                summary_data.append({
                                    'Metric Name': metric_name,
                                    'Current Value': 'Error',
                                    'Latest Date': 'Error',
                                    'Units': 'Error',
                                    'Frequency': 'Error',
                                    'Sequential Change': 'Error',
                                    'YTD Change': 'Error'
                                })
                        
                        if summary_data:
                            # Display summary table
                            summary_df = pd.DataFrame(summary_data)
                            st.dataframe(
                                summary_df,
                                width='stretch',
                                hide_index=True
                            )
                            
                            # Download button for summary
                            summary_csv = summary_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Summary as CSV",
                                data=summary_csv,
                                file_name="fred_metrics_summary.csv",
                                mime="text/csv",
                                key="download_summary"
                            )
                        else:
                            st.info("No summary data available.")
                    else:
                        st.info("No saved metrics to summarize. Add some metrics first!")
                    
            else:
                st.error(f"No data found for series ID: {series_id}")
                st.info("Please check the series ID and try again. Make sure it's a valid FRED identifier.")
    else:
        st.info("💡 Enter a FRED series ID above and it will automatically load, or use the Fetch Data button.")

if __name__ == "__main__":
    main()