import pandas as pd

class Process:
    def __init__(self, pid, ppid, burst_time, arrival_time, priority):
        self.pid = pid
        self.ppid = ppid
        self.burst_time = burst_time
        self.arrival_time = arrival_time
        self.original_priority = priority
        self.current_priority = priority
        self.remaining_time = burst_time
        self.start_time = -1
        self.completion_time = 0
        self.waiting_time = 0
        self.turnaround_time = 0
        self.is_completed = False

    def to_dict(self):
        return {
            "PID": self.pid,
            "PPID": self.ppid,
            "Burst Time": self.burst_time,
            "Arrival Time": self.arrival_time,
            "Original Priority": self.original_priority,
            "Final Priority": self.current_priority,
            "Waiting Time": self.waiting_time,
            "Turnaround Time": self.turnaround_time,
            "Completion Time": self.completion_time
        }

class Scheduler:
    def __init__(self):
        self.processes = []
        self.execution_log = [] # List of tuples (pid, start_time, end_time)
        self.starvation_log = [] # List of events explaining starvation

    def add_process(self, process):
        self.processes.append(process)

    def reset_processes(self):
        """Resets process state for re-simulation"""
        self.execution_log = []
        self.starvation_log = []
        for p in self.processes:
            p.remaining_time = p.burst_time
            p.start_time = -1
            p.completion_time = 0
            p.waiting_time = 0
            p.turnaround_time = 0
            p.is_completed = False
            p.current_priority = p.original_priority

    def run_fcfs(self):
        self.reset_processes()
        time = 0
        # Sort by arrival time
        sorted_processes = sorted(self.processes, key=lambda x: x.arrival_time)
        
        for p in sorted_processes:
            if time < p.arrival_time:
                time = p.arrival_time
            
            p.start_time = time
            self.execution_log.append((p.pid, time, time + p.burst_time))
            time += p.burst_time
            p.completion_time = time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            p.is_completed = True

    def run_sjf(self, aging_enabled=False, aging_interval=2, aging_step=1):
        """Shortest Job First (Non-Preemptive) with optional Aging"""
        self.reset_processes()
        current_time = 0
        completed = 0
        n = len(self.processes)
        ready_queue = []
        
        while completed < n:
            # Add arrivals
            for p in self.processes:
                if p.arrival_time <= current_time and not p.is_completed and p not in ready_queue:
                    # For SJF, initial 'current_priority' for sorting is the burst time
                    if aging_enabled:
                        p.current_priority = p.burst_time
                    ready_queue.append(p)
            
            if not ready_queue:
                current_time += 1
                continue
            
            # Aging Logic (Mirrors Priority Scheduling)
            if aging_enabled:
                for p in ready_queue:
                    wait_duration = current_time - p.arrival_time
                    # Decrease effective burst time (Priority for SJF) based on wait
                    reduction = (wait_duration // aging_interval) * aging_step
                    old_prio = p.current_priority
                    # Effective Burst Time cannot be negative
                    p.current_priority = max(0, p.burst_time - reduction)
                    
                    if p.current_priority != old_prio:
                        self.starvation_log.append({
                            "Time": current_time,
                            "PID": p.pid,
                            "Old Priority": old_prio,
                            "New Priority": p.current_priority, # Here Priority means Effective Burst Time
                            "Waited": wait_duration
                        })
                
                # Sort by Effective Burst Time (Ascending)
                ready_queue.sort(key=lambda x: x.current_priority)
            else:
                # Standard SJF: Sort by Burst Time
                ready_queue.sort(key=lambda x: x.burst_time)
            
            p = ready_queue.pop(0)
            p.start_time = current_time
            self.execution_log.append((p.pid, current_time, current_time + p.burst_time))
            current_time += p.burst_time
            p.completion_time = current_time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
            p.is_completed = True
            completed += 1

    def run_srtf(self, aging_enabled=False, aging_interval=2, aging_step=1):
        """Shortest Remaining Time First (Preemptive SJF) with optional Aging"""
        self.reset_processes()
        current_time = 0
        completed = 0
        n = len(self.processes)
        
        while completed < n:
            # Find process with min remaining time among arrived
            candidates = [p for p in self.processes if p.arrival_time <= current_time and not p.is_completed]
            
            if not candidates:
                current_time += 1
                continue
            
            # Aging Logic (for preemptive)
            if aging_enabled:
                for p in candidates:
                    # Calculate true waiting time (excluding execution time)
                    executed = p.burst_time - p.remaining_time
                    wait_duration = (current_time - p.arrival_time) - executed
                    
                    # Reduce effective remaining time based on wait
                    reduction = (wait_duration // aging_interval) * aging_step
                    old_prio = p.current_priority if hasattr(p, 'current_priority') and p.current_priority != p.original_priority else p.remaining_time
                    p.current_priority = max(0, p.remaining_time - reduction)
                    
                    if p.current_priority != old_prio:
                        self.starvation_log.append({
                            "Time": current_time,
                            "PID": p.pid,
                            "Old Priority": old_prio,
                            "New Priority": p.current_priority,
                            "Waited": wait_duration
                        })
                
                # Sort by Effective Remaining Time
                current_p = min(candidates, key=lambda x: x.current_priority)
            else:
                # Standard SRTF: Sort by Remaining Time
                current_p = min(candidates, key=lambda x: x.remaining_time)
            
            # Record execution slice
            self.execution_log.append((current_p.pid, current_time, current_time + 1))
            
            current_p.remaining_time -= 1
            current_time += 1
            
            if current_p.remaining_time == 0:
                current_p.completion_time = current_time
                current_p.turnaround_time = current_p.completion_time - current_p.arrival_time
                current_p.waiting_time = current_p.turnaround_time - current_p.burst_time
                current_p.is_completed = True
                completed += 1
                
    def run_round_robin(self, time_quantum=2, aging_enabled=False, aging_interval=2, aging_step=1):
        """Round Robin with optional Aging (Priority Queue)"""
        self.reset_processes()
        current_time = 0
        completed = 0
        n = len(self.processes)
        
        proc_list = sorted(self.processes, key=lambda x: x.arrival_time)
        queue = []
        idx = 0
        
        # Enqueue initial
        while idx < n and proc_list[idx].arrival_time <= current_time:
            queue.append(proc_list[idx])
            idx += 1
            
        while completed < n:
            if not queue:
                if idx < n:
                    current_time = proc_list[idx].arrival_time
                    while idx < n and proc_list[idx].arrival_time <= current_time:
                        queue.append(proc_list[idx])
                        idx += 1
                else:
                    current_time += 1
                continue
            
            # Aging Logic: Boost Priorities and Re-Sort Queue
            if aging_enabled:
                for p in queue:
                    # Approximation of waiting in queue: 
                    # Total Waiting = (Current Time - Arrival) - (Burst - Remaining)
                    executed = p.burst_time - p.remaining_time
                    wait_duration = (current_time - p.arrival_time) - executed
                    
                    boost = (wait_duration // aging_interval) * aging_step
                    old_prio = p.current_priority
                    p.current_priority = p.original_priority + boost
                    
                    if p.current_priority != old_prio:
                        self.starvation_log.append({
                            "Time": current_time,
                            "PID": p.pid,
                            "Old Priority": old_prio,
                            "New Priority": p.current_priority,
                            "Waited": wait_duration
                        })
                
                # Sort queue by Priority (Higher First)
                # Note: RR usually is stable, so sort stable?
                queue.sort(key=lambda x: x.current_priority, reverse=True)
                
            p = queue.pop(0)
            exec_time = min(time_quantum, p.remaining_time)
            
            self.execution_log.append((p.pid, current_time, current_time + exec_time))
            p.remaining_time -= exec_time
            current_time += exec_time
            
            # Check arrivals during execution
            while idx < n and proc_list[idx].arrival_time <= current_time:
                # If aging enabled, new arrivals enter with base priority?
                # We append, and they get sorted next cycle? 
                # Yes, but strict priority would want them sorted NOW if preemptive?
                # RR is non-preemptive within quantum. So append is fine for now.
                queue.append(proc_list[idx])
                idx += 1
                
            if p.remaining_time > 0:
                queue.append(p)
            else:
                p.completion_time = current_time
                p.turnaround_time = p.completion_time - p.arrival_time
                p.waiting_time = p.turnaround_time - p.burst_time
                p.is_completed = True
                completed += 1

    def run_priority_preemptive(self):
        """Priority (Preemptive) - Higher Value = Higher Priority"""
        self.reset_processes()
        current_time = 0
        completed = 0
        n = len(self.processes)
        
        while completed < n:
            candidates = [p for p in self.processes if p.arrival_time <= current_time and not p.is_completed]
            
            if not candidates:
                current_time += 1
                continue
            
            # Sort by Priority (Desc) then Arrival (Asc)
            current_p = max(candidates, key=lambda x: (x.current_priority, -x.arrival_time))
            
            self.execution_log.append((current_p.pid, current_time, current_time + 1))
            current_p.remaining_time -= 1
            current_time += 1
            
            if current_p.remaining_time == 0:
                current_p.completion_time = current_time
                current_p.turnaround_time = current_p.completion_time - current_p.arrival_time
                current_p.waiting_time = current_p.turnaround_time - current_p.burst_time
                current_p.is_completed = True
                completed += 1

    def run_priority_non_preemptive(self, aging_enabled=False, aging_interval=2, aging_step=1):
        self.reset_processes()
        current_time = 0
        completed = 0
        n = len(self.processes)
        ready_queue = []
        
        while completed < n:
            # Add newly arrived processes to ready queue
            for p in self.processes:
                if p.arrival_time <= current_time and not p.is_completed and p not in ready_queue:
                    ready_queue.append(p)
            
            if not ready_queue:
                current_time += 1
                continue

            # Check for starvation / apply aging if enabled
            if aging_enabled:
                for p in ready_queue:
                    # Simple aging logic: if waiting > threshold, increase priority (lower number is higher priority typically, 
                    # but let's assume HIGHER number is HIGHER priority for this visualizer unless specified.
                    # Standard Unix: Lower is higher. Windows: Higher is higher.
                    # Let's assume Higher Value = Higher Priority for clarity in visualization)
                    
                    time_waited = current_time - p.arrival_time
                    # If this process is not the one about to be picked, check if it's starving
                    # We'll stick to a simple periodic aging: every 'aging_interval' units of waiting, increase priority.
                    
                    # Calculate how many intervals have passed since arrival
                    # but typically aging happens if it sits in ready queue.
                    # Simplified: Increase priority of everyone in ready queue by 'aging_step' 
                    # IF they are not the one being picked? Or just periodically logic?
                    
                    # Logic: Increase priority of everyone in waiting queue
                    # In a tick-based simulation, we'd do this every tick. But this is event-based.
                    # Let's approximate: For every 'aging_interval' waits, boost priority.
                    pass 

            # Sort ready queue by Priority (Higher is Higher) -> Then FCFS
            # To handle aging properly in a non-preemptive logic without tick-by-tick simulation:
            # It's better to pick the candidate based on Current Priority.
            # But "Aging" implies dynamic change over time.
            # So, actually, without Preemption, 'Aging' decides WHO gets picked NEXT.
            
            # Application of Aging:
            # For all processes in ready queue, boost priority based on how long they've waited.
            if aging_enabled:
                 for p in ready_queue:
                     wait_duration = current_time - p.arrival_time
                     # Increase priority based on wait duration
                     boost = (wait_duration // aging_interval) * aging_step
                     old_prio = p.current_priority
                     p.current_priority = p.original_priority + boost
                     if p.current_priority != old_prio:
                         self.starvation_log.append({
                             "Time": current_time,
                             "PID": p.pid,
                             "Old Priority": old_prio,
                             "New Priority": p.current_priority,
                             "Waited": wait_duration
                         })

            # Pick highest priority
            ready_queue.sort(key=lambda x: x.current_priority, reverse=True)
            
            current_process = ready_queue[0]
            ready_queue.pop(0)
            
            # Execute
            current_process.start_time = current_time
            self.execution_log.append((current_process.pid, current_time, current_time + current_process.burst_time))
            current_time += current_process.burst_time
            current_process.completion_time = current_time
            current_process.turnaround_time = current_process.completion_time - current_process.arrival_time
            current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
            current_process.is_completed = True
            completed += 1

    def detect_starvation(self, starvation_threshold):
        """
        Analyze the inputs (Arrival, Priority) and Result (Waiting Time) to identify starvation.
        Starvation definition here: A process had to wait significantly longer than others with lower/same priority 
        OR simply waited > threshold despite being ready.
        """
        starved_processes = []
        for p in self.processes:
            if p.waiting_time > starvation_threshold:
                reason = f"Waited {p.waiting_time} units, exceeding threshold {starvation_threshold}."
                # Check if it was bypassed by higher priority processes
                higher_prio_count = len([x for x in self.processes if x.original_priority > p.original_priority])
                if higher_prio_count > 0:
                    reason += f" Likely starved by {higher_prio_count} higher priority processes."
                
                starved_processes.append({
                    "PID": p.pid,
                    "Waiting Time": p.waiting_time,
                    "Threshold": starvation_threshold,
                    "Blocked By": higher_prio_count,
                    "Reason": reason
                })
        return starved_processes

    def get_results_df(self):
        data = [p.to_dict() for p in self.processes]
        return pd.DataFrame(data)
