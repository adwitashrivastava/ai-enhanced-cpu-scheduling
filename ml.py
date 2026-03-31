"""
Sentient OS Scheduler (Paper-Aligned Implementation)

Implements:
1. Traditional Round Robin (baseline)
2. AI-Enhanced ADRR scheduler (paper methodology)

Additions vs old code:
- Decision Tree burst prediction
- ADRR uses predicted bursts
- Hybrid RR fallback when variance low
"""

import random
from collections import deque
import numpy as np
from sklearn.tree import DecisionTreeRegressor


# ===============================
# Process Model
# ===============================
class Process:
    def __init__(self, pid, arrival_time, burst_time, priority=0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.original_burst_time = burst_time
        self.remaining_burst_time = burst_time
        self.predicted_burst_time = burst_time
        self.priority = priority

        self.completion_time = 0
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = -1
        self.first_execution = True

    def reset(self):
        self.remaining_burst_time = self.original_burst_time
        self.first_execution = True


# ===============================
# ML Burst Predictor
# ===============================
class BurstTimePredictor:
    def __init__(self):
        self.model = DecisionTreeRegressor(max_depth=5)

    def train(self, processes):
        X = [[p.arrival_time, p.priority] for p in processes]
        y = [p.original_burst_time for p in processes]
        self.model.fit(X, y)

    def predict(self, process):
        X = [[process.arrival_time, process.priority]]
        return max(1, int(self.model.predict(X)[0]))


# ===============================
# Round Robin Scheduler
# ===============================
class RoundRobinScheduler:
    def __init__(self, time_quantum=4):
        self.time_quantum = time_quantum

    def schedule(self, processes):
        processes = [Process(p.pid, p.arrival_time, p.original_burst_time, p.priority) for p in processes]

        ready_queue = deque()
        remaining = sorted(processes, key=lambda x: x.arrival_time)

        time = 0
        context_switches = 0
        completed = []

        while remaining or ready_queue:

            while remaining and remaining[0].arrival_time <= time:
                ready_queue.append(remaining.pop(0))

            if not ready_queue:
                time = remaining[0].arrival_time
                continue

            p = ready_queue.popleft()

            if p.first_execution:
                p.response_time = time - p.arrival_time
                p.first_execution = False

            exec_time = min(self.time_quantum, p.remaining_burst_time)
            p.remaining_burst_time -= exec_time
            time += exec_time

            while remaining and remaining[0].arrival_time <= time:
                ready_queue.append(remaining.pop(0))

            if p.remaining_burst_time > 0:
                ready_queue.append(p)
                context_switches += 1
            else:
                p.completion_time = time
                p.turnaround_time = time - p.arrival_time
                p.waiting_time = p.turnaround_time - p.original_burst_time
                completed.append(p)

        return completed, context_switches


# ===============================
# AI-Enhanced ADRR Scheduler
# ===============================
class ADRRScheduler:
    def calculate_time_quantum(self, queue):
        if len(queue) <= 1:
            return 4

        bursts = [p.predicted_burst_time for p in queue]

        diffs = [abs(bursts[i] - bursts[i + 1]) for i in range(len(bursts) - 1)]
        avg_diff = sum(diffs) / len(diffs)

        if avg_diff > 12:
            return 10
        elif avg_diff > 6:
            return 8
        elif avg_diff > 3:
            return 6
        else:
            return 4

    def schedule(self, processes):

        processes = [Process(p.pid, p.arrival_time, p.original_burst_time, p.priority) for p in processes]

        ready_queue = deque()
        remaining = sorted(processes, key=lambda x: x.arrival_time)

        time = 0
        context_switches = 0
        completed = []

        while remaining or ready_queue:

            while remaining and remaining[0].arrival_time <= time:
                ready_queue.append(remaining.pop(0))

            if not ready_queue:
                time = remaining[0].arrival_time
                continue

            # Hybrid fallback: if low variance → behave like RR
            variance = np.var([p.predicted_burst_time for p in ready_queue])
            if variance < 5:
                tq = 4
            else:
                tq = self.calculate_time_quantum(list(ready_queue))

            p = ready_queue.popleft()

            if p.first_execution:
                p.response_time = time - p.arrival_time
                p.first_execution = False

            exec_time = min(tq, p.remaining_burst_time)
            p.remaining_burst_time -= exec_time
            time += exec_time

            while remaining and remaining[0].arrival_time <= time:
                ready_queue.append(remaining.pop(0))

            if p.remaining_burst_time > 0:
                ready_queue.append(p)
                context_switches += 1
            else:
                p.completion_time = time
                p.turnaround_time = time - p.arrival_time
                p.waiting_time = p.turnaround_time - p.original_burst_time
                completed.append(p)

        return completed, context_switches


# ===============================
# Metrics
# ===============================
def calculate_metrics(procs):
    n = len(procs)

    avg_wt = sum(p.waiting_time for p in procs) / n
    avg_tat = sum(p.turnaround_time for p in procs) / n
    avg_rt = sum(p.response_time for p in procs) / n

    total_burst = sum(p.original_burst_time for p in procs)
    total_time = max(p.completion_time for p in procs)
    cpu_util = (total_burst / total_time) * 100

    return avg_wt, avg_tat, avg_rt, cpu_util

def print_results_table(rr_metrics, adrr_metrics, rr_cs, adrr_cs):
    print("\n" + "="*72)
    print("RR vs AI-ADRR PERFORMANCE COMPARISON")
    print("="*72)

    headers = [
        "Metric",
        "Round Robin",
        "AI-Enhanced ADRR"
    ]

    table = [
        ["Avg Waiting Time", f"{rr_metrics[0]:.2f}", f"{adrr_metrics[0]:.2f}"],
        ["Avg Turnaround Time", f"{rr_metrics[1]:.2f}", f"{adrr_metrics[1]:.2f}"],
        ["Avg Response Time", f"{rr_metrics[2]:.2f}", f"{adrr_metrics[2]:.2f}"],
        ["CPU Utilization (%)", f"{rr_metrics[3]:.2f}", f"{adrr_metrics[3]:.2f}"],
        ["Context Switches", rr_cs, adrr_cs],
    ]

    print(f"{headers[0]:<25}{headers[1]:<20}{headers[2]:<20}")
    print("-"*72)   

    for row in table:
        print(f"{row[0]:<25}{row[1]:<20}{row[2]:<20}")

    print("="*72)


# ===============================
# Process Generator
# ===============================
def generate_processes(n=12, seed=42):
    random.seed(seed)
    processes = []

    for i in range(n):
        arrival = random.randint(0, 15)
        burst = random.randint(3, 35)
        priority = random.randint(1, 5)
        processes.append(Process(i + 1, arrival, burst, priority))

    return processes


# ===============================
# Main
# ===============================
def main():
    processes = generate_processes()

    # Train ML model
    predictor = BurstTimePredictor()
    predictor.train(processes)

    for p in processes:
        p.predicted_burst_time = predictor.predict(p)

    print("\nPredicted Burst Times:")
    for p in processes:
        print(f"P{p.pid}: actual={p.original_burst_time}, predicted={p.predicted_burst_time}")

    # RR
    rr = RoundRobinScheduler()
    rr_done, rr_cs = rr.schedule(processes)
    rr_metrics = calculate_metrics(rr_done)

    # ADRR
    adrr = ADRRScheduler()
    adrr_done, adrr_cs = adrr.schedule(processes)
    adrr_metrics = calculate_metrics(adrr_done)

    print_results_table(rr_metrics, adrr_metrics, rr_cs, adrr_cs)

    print_improvements(rr_metrics, adrr_metrics, rr_cs, adrr_cs)

def print_improvements(rr_metrics, adrr_metrics, rr_cs, adrr_cs):
    wt_improve = ((rr_metrics[0] - adrr_metrics[0]) / rr_metrics[0]) * 100
    tat_improve = ((rr_metrics[1] - adrr_metrics[1]) / rr_metrics[1]) * 100
    cs_improve = ((rr_cs - adrr_cs) / rr_cs) * 100

    print("\nIMPROVEMENTS (AI-ADRR over RR)")
    print("-"*40)
    print(f"Waiting Time Reduction: {wt_improve:.2f}%")
    print(f"Turnaround Time Reduction: {tat_improve:.2f}%")
    print(f"Context Switch Reduction: {cs_improve:.2f}%")
    print("-"*40)

if __name__ == "__main__":
    main()
