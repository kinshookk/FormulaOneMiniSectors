import fastf1
import fastf1.plotting
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.patches as mpatches

# Enable FastF1 cache
fastf1.Cache.enable_cache('cache')
fastf1.plotting.setup_mpl()

def get_available_events(year):
    """Get all available events for a given year."""
    schedule = fastf1.get_event_schedule(year)
    return schedule['EventName'].tolist()


def format_time(seconds):
    """Convert seconds to mm:ss:ms format."""
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{minutes:02}:{remaining_seconds:02}:{milliseconds:03}"



def create_minisector_plot(session, num_minisectors=25):
    """Create minisector comparison plot between pole sitter and P2."""
    # Get qualifying results to identify P1 and P2
    results = session.results
    p1_driver = results.iloc[0]['Abbreviation']
    p2_driver = results.iloc[1]['Abbreviation']
    
    # Get fastest laps
    p1_lap = session.laps.pick_driver(p1_driver).pick_fastest()
    p2_lap = session.laps.pick_driver(p2_driver).pick_fastest()
    
    # Get telemetry
    p1_tel = p1_lap.get_telemetry()
    p2_tel = p2_lap.get_telemetry()
    
    # Convert distance to float
    p1_tel['Distance'] = p1_tel['Distance'].astype(float)
    p2_tel['Distance'] = p2_tel['Distance'].astype(float)
    
    # Add driver labels
    p1_tel['Driver'] = p1_driver
    p2_tel['Driver'] = p2_driver
    
    # Combine telemetry data
    telemetry = pd.concat([p1_tel, p2_tel])
    
    # Calculate minisectors
    total_distance = max(telemetry['Distance'])
    minisector_length = total_distance / num_minisectors
    minisectors = [i * minisector_length for i in range(num_minisectors + 1)]
    
    telemetry['Minisector'] = pd.cut(telemetry['Distance'],
                                    bins=minisectors,
                                    labels=range(1, num_minisectors + 1))
    
    # Calculate fastest driver per minisector
    average_speed = telemetry.groupby(['Minisector', 'Driver'])['Speed'].mean().reset_index()
    fastest_driver = average_speed.loc[average_speed.groupby('Minisector')['Speed'].idxmax()]
    fastest_driver = fastest_driver[['Minisector', 'Driver']]
    
    # Count sectors won by each driver
    p1_sectors = len(fastest_driver[fastest_driver['Driver'] == p1_driver])
    p2_sectors = len(fastest_driver[fastest_driver['Driver'] == p2_driver])
    
    # Merge fastest driver info
    telemetry = telemetry.merge(fastest_driver, on=['Minisector'], suffixes=('', '_fastest'))
    telemetry['Fastest_driver_int'] = telemetry['Driver_fastest'].map({p1_driver: 1, p2_driver: 2})
    
    # Create the plot
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(20, 12))
    
    # Plot track
    x = np.array(telemetry['X'].values)
    y = np.array(telemetry['Y'].values)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    fastest_driver_array = telemetry['Fastest_driver_int'].to_numpy().astype(float)
    
    # Define fixed colors for consistency
    p1_color = '#FF1E1E'  # Red
    p2_color = '#00FF00'  # Green
    
    colors = [p1_color, p2_color]
    cmap = plt.cm.colors.ListedColormap(colors)
    
    lc_comp = LineCollection(segments, norm=plt.Normalize(1, 2), cmap=cmap)
    lc_comp.set_array(fastest_driver_array)
    lc_comp.set_linewidth(5)
    
    ax.add_collection(lc_comp)
    ax.axis('equal')
    ax.set_axis_off()
    
    # Add title and statistics
    plt.suptitle(f"{session.event['EventName']} {session.event.year} Qualification\nFastest Driver per Minisector",
                y=0.95, fontsize=20, fontweight='bold')
    
    stats_text = f'Minisector Comparison ({num_minisectors} sectors)\n'
    stats_text += f'{p1_driver}: {p1_sectors} sectors ({p1_sectors/num_minisectors*100:.1f}%)\n'
    stats_text += f'{p2_driver}: {p2_sectors} sectors ({p2_sectors/num_minisectors*100:.1f}%)'
    
    plt.figtext(0.12, 0.12, stats_text, fontsize=12, bbox=dict(facecolor='black', alpha=0.7))
    
    # Add legend
    p1_patch = mpatches.Patch(color=colors[0], label=f'{p1_driver} Faster')
    p2_patch = mpatches.Patch(color=colors[1], label=f'{p2_driver} Faster')
    legend = plt.legend(handles=[p1_patch, p2_patch],
                       loc='lower right',
                       bbox_to_anchor=(0.95, 0.12),
                       framealpha=0.7)
    
    # Add lap times
    p1_time_str = format_time(p1_lap['LapTime'].total_seconds())
    p2_time_str = format_time(p2_lap['LapTime'].total_seconds())
    delta_time_str = format_time(abs(p1_lap['LapTime'].total_seconds() - p2_lap['LapTime'].total_seconds()))
    time_text = f"Lap Times:\n{p1_driver}: {p1_time_str}\n{p2_driver}: {p2_time_str}\nDelta: {delta_time_str}"
    plt.figtext(0.12, 0.25, time_text, fontsize=12, bbox=dict(facecolor='black', alpha=0.7))
    
    # Calculate the track direction based on two distinct points
    idx_start = int(len(x) * 0.2)  # Start at 20% of the track
    idx_end = int(len(x) * 0.3)    # End at 30% of the track
    direction_x = x[idx_end] - x[idx_start]
    direction_y = y[idx_end] - y[idx_start]

    # Normalize direction vector for arrow length
    dir_magnitude = np.sqrt(direction_x**2 + direction_y**2)
    direction_x = (direction_x / dir_magnitude) * 1500  # Increase scale for better visibility
    direction_y = (direction_y / dir_magnitude) * 1500

    # Place the arrow at a specific point on the track to ensure visibility
    arrow_pos_idx = int(len(x) * 0.25)
    arrow_x = x[arrow_pos_idx]
    arrow_y = y[arrow_pos_idx]

    # Add the white track direction arrow
    ax.arrow(arrow_x, arrow_y, 
            direction_x, direction_y, 
            head_width=50, head_length=50, fc='white', ec='white', 
            alpha=0.9, length_includes_head=True)

    # Add the track direction label near the arrow
    plt.text(arrow_x + direction_x * 0.1, 
            arrow_y + direction_y * 0.1, 
            'Track Direction', 
            color='white', 
            ha='center', 
            va='center', 
            fontsize=12, 
            fontweight='bold')



    
    return fig
