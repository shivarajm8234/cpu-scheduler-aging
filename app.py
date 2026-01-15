import streamlit as st
import pandas as pd
import plotly.express as px
import psutil
import random
from scheduler import Process, Scheduler

st.set_page_config(page_title="Smart CPU Scheduler", layout="wide")

st.title("Smart CPU Scheduler & Starvation Visualizer")
st.markdown("""
This application simulates a CPU scheduler to demonstrate **Starvation** and **Aging**.
1. **Starvation**: Occurs when low-priority processes wait indefinitely because high-priority processes keep arriving.
2. **Aging**: A technique to resolve starvation by gradually increasing the priority of waiting processes.
""")

# Initialize Session State
if 'scheduler' not in st.session_state:
    st.session_state.scheduler = Scheduler()
if 'processes_data' not in st.session_state:
    st.session_state.processes_data = []

# Sidebar - Config
st.sidebar.header("Configuration")
algorithm_choice = st.sidebar.selectbox("Scheduling Algorithm", [
    "FCFS", 
    "SJF (Non-Preemptive)", 
    "SRTF (Preemptive SJF)", 
    "Round Robin", 
    "Priority (Non-Preemptive)", 
    "Priority (Preemptive)"
])

time_quantum = 2
if algorithm_choice == "Round Robin":
    time_quantum = st.sidebar.number_input("Time Quantum", min_value=1, value=2)

starvation_threshold = st.sidebar.number_input("Starvation Threshold (Wait Time)", min_value=1, value=10, help="Processes waiting longer than this are considered starved.")
aging_interval = st.sidebar.number_input("Aging Interval", min_value=1, value=2, help="Every X time units of waiting, increase priority.")
aging_step = st.sidebar.number_input("Aging Step", min_value=1, value=1, help="Amount to increase priority by.")

# Sidebar - Input
st.sidebar.header("Add Process")
pid = st.sidebar.text_input("PID", value=f"P{len(st.session_state.processes_data)+1}")
ppid = st.sidebar.text_input("PPID", value="0")
burst_time = st.sidebar.number_input("Burst Time", min_value=1, value=5)
arrival_time = st.sidebar.number_input("Arrival Time", min_value=0, value=0)
priority = st.sidebar.number_input("Priority (Higher = More Important)", min_value=1, value=1)

if st.sidebar.button("Add Process"):
    new_process = {
        "pid": pid,
        "ppid": ppid,
        "burst_time": burst_time,
        "arrival_time": arrival_time,
        "priority": priority
    }
    st.session_state.processes_data.append(new_process)
    st.success(f"Added Process {pid}")

if st.sidebar.button("Fetch System Processes (Random 10)"):
    try:
        st.session_state.processes_data = []
        count = 0
        for proc in psutil.process_iter(['pid', 'ppid', 'name', 'nice']):
            try:
                if count >= 10: break
                nice = proc.info.get('nice', 0) or 0
                if nice < 0: p_val = 10
                elif nice == 0: p_val = 5
                else: p_val = 1
                
                new_process = {
                    "pid": f"{proc.info['name']} ({proc.info['pid']})",
                    "ppid": str(proc.info['ppid']),
                    "burst_time": random.randint(2, 10),
                    "arrival_time": random.randint(0, 15),
                    "priority": p_val
                }
                st.session_state.processes_data.append(new_process)
                count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        st.success(f"Fetched {len(st.session_state.processes_data)} system processes with random arrival times.")
        st.rerun()
    except Exception as e:
        st.error(f"Error fetching processes: {e}")

if st.sidebar.button("Reset Processes"):
    st.session_state.processes_data = []
    st.session_state.scheduler = Scheduler()
    st.rerun()

# Main Area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Process Queue")
    if st.session_state.processes_data:
        input_df = pd.DataFrame(st.session_state.processes_data)
        st.dataframe(input_df)
    else:
        st.info("No processes added yet.")

# Simulation Logic
if st.session_state.processes_data:
    st.markdown("---")
    st.subheader("Simulation Results")
    
    # Init Schedulers
    # scheduler_main: Runs the selected algorithm (No Aging, typically)
    # scheduler_aging: Runs ONLY if Priority algorithm selected, to show 'With Aging' comparison.
    scheduler_main = Scheduler()
    scheduler_aging_sim = Scheduler()
    
    for p_data in st.session_state.processes_data:
        p = Process(p_data['pid'], p_data['ppid'], p_data['burst_time'], p_data['arrival_time'], p_data['priority'])
        scheduler_main.add_process(p)
        # Clone for aging sim
        p2 = Process(p_data['pid'], p_data['ppid'], p_data['burst_time'], p_data['arrival_time'], p_data['priority'])
        scheduler_aging_sim.add_process(p2)
    
    # Execute Main Algorithm
    if algorithm_choice == "FCFS":
        scheduler_main.run_fcfs()
    elif algorithm_choice == "SJF (Non-Preemptive)":
        scheduler_main.run_sjf()
    elif algorithm_choice == "SRTF (Preemptive SJF)":
        scheduler_main.run_srtf()
    elif algorithm_choice == "Round Robin":
        scheduler_main.run_round_robin(time_quantum=time_quantum)
    elif algorithm_choice == "Priority (Non-Preemptive)":
        scheduler_main.run_priority_non_preemptive(aging_enabled=False)
    elif algorithm_choice == "Priority (Preemptive)":
        scheduler_main.run_priority_preemptive()
        
    # Execute Aging Sim (For Priority, SJF, SRTF, and Round Robin)
    is_aging_applicable = algorithm_choice in ["Priority (Non-Preemptive)", "Priority (Preemptive)", "SJF (Non-Preemptive)", "SRTF (Preemptive SJF)", "Round Robin"]
    
    if is_aging_applicable:
        if algorithm_choice == "Priority (Non-Preemptive)":
            scheduler_aging_sim.run_priority_non_preemptive(aging_enabled=True, aging_interval=aging_interval, aging_step=aging_step)
        elif algorithm_choice == "Priority (Preemptive)":
            scheduler_aging_sim.run_priority_non_preemptive(aging_enabled=True, aging_interval=aging_interval, aging_step=aging_step)
        elif algorithm_choice == "SJF (Non-Preemptive)":
            scheduler_aging_sim.run_sjf(aging_enabled=True, aging_interval=aging_interval, aging_step=aging_step)
        elif algorithm_choice == "SRTF (Preemptive SJF)":
            scheduler_aging_sim.run_srtf(aging_enabled=True, aging_interval=aging_interval, aging_step=aging_step)
        elif algorithm_choice == "Round Robin":
            scheduler_aging_sim.run_round_robin(time_quantum=time_quantum, aging_enabled=True, aging_interval=aging_interval, aging_step=aging_step)
        
    # Tabs
    tabs = ["Execution (Gantt)", "Starvation Analysis", "CPU Heatmap", "Export"]
    if is_aging_applicable:
        tabs.insert(2, "Aging Effect")
        
    tab_list = st.tabs(tabs)
    
    # 1. Gantt Chart (Tab 0)
    with tab_list[0]:
        st.write(f"### Execution Timeline ({algorithm_choice})")
        if scheduler_main.execution_log:
            df_gantt = pd.DataFrame(scheduler_main.execution_log, columns=['Task', 'Start', 'Finish'])
            df_gantt['Duration'] = df_gantt['Finish'] - df_gantt['Start']
            df_gantt['Resource'] = 'CPU'
            
            fig = px.bar(df_gantt, x="Duration", y="Resource", base="Start", color="Task", 
                          text="Task", title=f"Gantt Chart ({algorithm_choice})", orientation='h')
            fig.update_traces(textposition='inside', insidetextanchor='middle')
            fig.update_layout(xaxis_title="Time (Ticks)", yaxis_title="Resource", showlegend=True, xaxis=dict(showgrid=True))
            st.plotly_chart(fig, use_container_width=True, key="gantt_main")

    # 2. Starvation Analysis (Tab 1)
    with tab_list[1]:
        st.write("### Starvation Detection")
        starved = scheduler_main.detect_starvation(starvation_threshold)
        if starved:
            starved_df = pd.DataFrame(starved)
            st.dataframe(starved_df, use_container_width=True)
            
            fig_starved = px.bar(starved_df, x='PID', y='Waiting Time', color='Blocked By' if 'Blocked By' in starved_df.columns else None,
                                 title="Starved Processes Wait Time", hover_data=['Reason'])
            fig_starved.add_hline(y=starvation_threshold, line_dash="dash", line_color="red", annotation_text="Threshold")
            st.plotly_chart(fig_starved, use_container_width=True, key="starvation_chart")
        else:
            st.success("No starvation detected (or threshold too high).")
        
        st.write("### Performance Metrics")
        st.markdown("""
        **Key Metrics Definition:**
        - **Waiting Time**: Total time a process spent in the ready queue waiting for CPU.
        - **Turnaround Time**: Total time from arrival to completion (Waiting Time + Burst Time).
        - **Completion Time**: The specific time unit when the process finished execution.
        """)
        res_df = scheduler_main.get_results_df()
        st.dataframe(res_df[['PID', 'Burst Time', 'Waiting Time', 'Turnaround Time', 'Completion Time']])

    # 3. Aging Effect (Tab 2, only if applicable)
    current_tab_idx = 2
    if is_aging_applicable:
        with tab_list[current_tab_idx]:
            st.write(f"### Aging Visualizer ({algorithm_choice})")
            
            if "SJF" in algorithm_choice or "SRTF" in algorithm_choice:
                st.markdown("""
                **Aging in SJF/SRTF:**
                
                **Problem:** Long processes starve because shorter jobs keep getting selected.
                
                **Solution:** Aging reduces the "effective burst time" of waiting processes, making them appear shorter over time.
                
                **How it works:** Every `Aging Interval` time units, a waiting process's effective burst time decreases by `Aging Step`. 
                Eventually, even a long job becomes the "shortest" and gets executed.
                """)
            elif algorithm_choice == "Round Robin":
                st.markdown("""
                **Aging in Round Robin:**
                
                **Problem:** Standard Round Robin doesn't prioritize processes that have been waiting longer overall.
                
                **Solution:** Aging adds priority to the queue - processes that wait longer get higher priority and move to the front.
                
                **How it works:** Every `Aging Interval` time units, a waiting process's priority increases by `Aging Step`. 
                The queue is sorted by priority, so long-waiting processes get their time slice sooner.
                """)
            else:
                st.markdown("""
                **Aging in Priority Scheduling:**
                
                **Problem:** Low-priority processes starve because high-priority processes keep arriving and getting executed first.
                
                **Solution:** Aging gradually increases the priority of waiting processes.
                
                **How it works:** Every `Aging Interval` time units, a waiting process's priority increases by `Aging Step`. 
                Eventually, even a low-priority process will have high enough priority to be selected.
                """)

            st.write("#### Execution Timeline (With Aging)")
            if scheduler_aging_sim.execution_log:
                df_gantt_age = pd.DataFrame(scheduler_aging_sim.execution_log, columns=['Task', 'Start', 'Finish'])
                df_gantt_age['Duration'] = df_gantt_age['Finish'] - df_gantt_age['Start']
                df_gantt_age['Resource'] = 'CPU'
                
                fig2 = px.bar(df_gantt_age, x="Duration", y="Resource", base="Start", color="Task", 
                              text="Task", title="Gantt Chart (With Aging)", orientation='h')
                fig2.update_layout(xaxis_title="Time (Ticks)", xaxis=dict(showgrid=True))
                st.plotly_chart(fig2, use_container_width=True, key="gantt_aging")

            # Improvement Metrics
            res_df_aging = scheduler_aging_sim.get_results_df()
            merged_metrics = pd.merge(res_df[['PID', 'Waiting Time']], res_df_aging[['PID', 'Waiting Time']], on='PID', suffixes=('_no_aging', '_aging'))
            merged_metrics['Time Saved'] = merged_metrics['Waiting Time_no_aging'] - merged_metrics['Waiting Time_aging']
            improved_count = merged_metrics[merged_metrics['Time Saved'] > 0].shape[0]
            st.metric(label="Processes Saved from Starvation", value=improved_count)
            
            # Detailed Comparison Tables
            st.write("#### Metrics Comparison: Without Aging vs With Aging")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Without Aging**")
                st.dataframe(res_df[['PID', 'Burst Time', 'Waiting Time', 'Turnaround Time', 'Completion Time']], use_container_width=True)
            
            with col2:
                st.write("**With Aging**")
                st.dataframe(res_df_aging[['PID', 'Burst Time', 'Waiting Time', 'Turnaround Time', 'Completion Time']], use_container_width=True)
            
            # Improvement Details
            st.write("#### Improvement Details")
            if improved_count > 0:
                improved_df = merged_metrics[merged_metrics['Time Saved'] > 0].copy()
                st.dataframe(improved_df[['PID', 'Waiting Time_no_aging', 'Waiting Time_aging', 'Time Saved']], use_container_width=True)
            else:
                st.info("No processes showed improvement. Try increasing the Aging Step or decreasing the Aging Interval.")
            
        current_tab_idx += 1

    # 4. CPU Heatmap
    with tab_list[current_tab_idx]:
        st.write("### CPU Usage Heatmap")
        if scheduler_main.execution_log:
            max_t = max([x[2] for x in scheduler_main.execution_log])
            procs = sorted(list(set([p['pid'] for p in st.session_state.processes_data])))
            
            heatmap_data = []
            for t in range(max_t + 1):
                for p_label in procs:
                    status = 0
                    for run in scheduler_main.execution_log:
                        if run[0] == p_label and run[1] <= t < run[2]:
                            status = 1
                            break
                    heatmap_data.append({"Time": t, "PID": p_label, "Status": status})
            
            df_heat = pd.DataFrame(heatmap_data)
            fig_heat = px.density_heatmap(df_heat, x="Time", y="PID", z="Status", 
                                          title="CPU Utilization Heatmap (1=Running)",
                                          color_continuous_scale="Viridis", labels={"Status": "Active"})
            fig_heat.update_layout(yaxis=dict(categoryorder='category ascending'))
            fig_heat.update_traces(xgap=3, ygap=3) # Add white spacing between blocks
            st.plotly_chart(fig_heat, use_container_width=True, key="heatmap")
        else:
            st.info("Run simulation to generate heatmap.")
    
    current_tab_idx += 1

    # 5. Export
    with tab_list[current_tab_idx]:
        st.write("### Export Results")
        export_df = scheduler_main.get_results_df()
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Simulation Results (CSV)",
            data=csv,
            file_name='cpu_scheduling_results.csv',
            mime='text/csv',
        )

