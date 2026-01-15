# Smart CPU Scheduler with Starvation Detection & Aging

A comprehensive CPU scheduling simulator built with Python and Streamlit that demonstrates various scheduling algorithms, starvation detection, and aging mechanisms.

## Features

### Scheduling Algorithms
- **FCFS** (First-Come, First-Served)
- **SJF** (Shortest Job First - Non-Preemptive)
- **SRTF** (Shortest Remaining Time First - Preemptive SJF)
- **Round Robin** (with configurable time quantum)
- **Priority Scheduling** (Non-Preemptive and Preemptive)

### Key Capabilities
- **Starvation Detection**: Identifies processes waiting beyond a configurable threshold
- **Aging Mechanism**: Prevents starvation by:
  - Reducing effective burst time (SJF/SRTF)
  - Increasing priority (Priority Scheduling, Round Robin)
- **Real Process Fetching**: Fetch actual system processes using `psutil`
- **Visual Comparisons**: Side-by-side Gantt charts with and without aging
- **CPU Heatmap**: Visualize CPU utilization over time
- **Export Results**: Download simulation results as CSV

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd os
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

Then:
1. Select a scheduling algorithm from the sidebar
2. Configure aging parameters (interval and step)
3. Add processes manually or fetch system processes
4. View results in multiple tabs:
   - **Execution (Gantt)**: Timeline visualization
   - **Starvation Analysis**: Detect starved processes
   - **Aging Effect**: Compare with/without aging
   - **CPU Heatmap**: Resource utilization
   - **Export**: Download results

## Project Structure

```
os-/
├── app.py              # Streamlit frontend
├── scheduler.py        # Core scheduling algorithms
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Configuration

- **Starvation Threshold**: Waiting time threshold for starvation detection
- **Aging Interval**: How often aging occurs (time units)
- **Aging Step**: How much priority/burst time changes per interval
- **Time Quantum**: Time slice for Round Robin (when selected)

## Educational Value

Each algorithm's aging mechanism includes:
- Problem statement (why starvation occurs)
- Solution overview (how aging helps)
- Mechanism details (technical implementation)
- Live comparison tables showing improvement

## Technologies

- **Python 3.x**
- **Streamlit**: Web interface
- **Pandas**: Data manipulation
- **Plotly**: Interactive visualizations
- **psutil**: System process information

## License

This project is for educational purposes.
