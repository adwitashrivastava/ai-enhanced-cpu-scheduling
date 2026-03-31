import pandas as pd
import numpy as np
from collections import deque
from sklearn import datasets
from sklearn.tree import DecisionTreeRegressor
import random
random.seed(42)

# =====================================================
# PROCESS MODEL
# =====================================================

class Process:

    def __init__(self, pid, arrival_time, burst_time, priority=1):

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


# =====================================================
# LOAD DATASET
# =====================================================

def load_processes_from_csv(path):

    df = pd.read_csv(path)

    df.columns = df.columns.str.strip().str.lower()

    print("\nDetected Columns:", df.columns.tolist())

    processes = []

    for i, row in df.iterrows():

        pid = i + 1

        arrival = int(row["arrival"])
        burst = int(row["burst"])
        priority = int(row["priority"])

        # scale timestamps
        arrival = arrival // 1000
        burst = max(1, burst)

        processes.append(
            Process(pid, arrival, burst, priority)
        )

    return processes

import random

# -------------------------------
# LOW VARIANCE DATASET
# -------------------------------
def low_variance_dataset(processes):

    new = []

    for p in processes:
        new.append(
            Process(
                p.pid,
                p.arrival_time,
                300,            # constant burst
                p.priority
            )
        )

    return new


# -------------------------------
# MODERATE VARIANCE DATASET
# -------------------------------
def moderate_variance_dataset(processes):

    new = []

    for p in processes:

        factor = random.uniform(0.7, 1.3)

        new.append(
            Process(
                p.pid,
                p.arrival_time,
                int(p.original_burst_time * factor),
                p.priority
            )
        )

    return new


# -------------------------------
# HIGH VARIANCE DATASET
# -------------------------------
def high_variance_dataset(processes):

    new = []

    for p in processes:

        r = random.random()

        burst = p.original_burst_time

        if r < 0.3:
            burst = burst // 5        # very short jobs
        elif r > 0.7:
            burst = burst * 5         # very long jobs

        new.append(
            Process(
                p.pid,
                p.arrival_time,
                max(1, burst),
                p.priority
            )
        )

    return new
# =====================================================
# ML BURST PREDICTOR
# =====================================================

class BurstTimePredictor:

    def __init__(self):
        self.model = DecisionTreeRegressor(max_depth=5)

    def train(self, processes):

        X = [[p.arrival_time, p.priority] for p in processes]
        y = [p.original_burst_time for p in processes]

        self.model.fit(X, y)

    def predict(self, process):

        X = [[process.arrival_time, process.priority]]

        return max(
            1,
            int(self.model.predict(X)[0])
        )


# =====================================================
# ROUND ROBIN
# =====================================================

class RoundRobinScheduler:

    def __init__(self, quantum=4):
        self.quantum = quantum

    def schedule(self, processes):

        processes = [
            Process(p.pid, p.arrival_time,
                    p.original_burst_time, p.priority)
            for p in processes
        ]

        ready = deque()
        remaining = sorted(processes,
                           key=lambda x: x.arrival_time)

        time = 0
        context_switches = 0
        completed = []

        while remaining or ready:

            while remaining and remaining[0].arrival_time <= time:
                ready.append(remaining.pop(0))

            if not ready:
                time = remaining[0].arrival_time
                continue

            p = ready.popleft()

            if p.first_execution:
                p.response_time = time - p.arrival_time
                p.first_execution = False

            exec_time = min(self.quantum,
                            p.remaining_burst_time)

            p.remaining_burst_time -= exec_time
            time += exec_time

            while remaining and remaining[0].arrival_time <= time:
                ready.append(remaining.pop(0))

            if p.remaining_burst_time > 0:
                ready.append(p)
                context_switches += 1

            else:
                p.completion_time = time
                p.turnaround_time = time - p.arrival_time
                p.waiting_time = (
                        p.turnaround_time -
                        p.original_burst_time
                )
                completed.append(p)

        return completed, context_switches


# =====================================================
# ADRR
# =====================================================

class ADRRScheduler:

    def calculate_quantum(self, queue):

        if len(queue) <= 1:
            return 4

        bursts = [p.remaining_burst_time for p in queue]

        diffs = [
            abs(bursts[i] - bursts[i+1])
            for i in range(len(bursts)-1)
        ]

        avg = sum(diffs) / len(diffs)

        if avg > 12:
            return 10
        elif avg > 6:
            return 8
        elif avg > 3:
            return 6
        return 4

    def schedule(self, processes):

        processes = [
            Process(p.pid, p.arrival_time,
                    p.original_burst_time, p.priority)
            for p in processes
        ]

        ready = deque()
        remaining = sorted(processes,
                           key=lambda x: x.arrival_time)

        time = 0
        context_switches = 0
        completed = []

        while remaining or ready:

            while remaining and remaining[0].arrival_time <= time:
                ready.append(remaining.pop(0))

            if not ready:
                time = remaining[0].arrival_time
                continue

            tq = self.calculate_quantum(list(ready))

            p = ready.popleft()

            if p.first_execution:
                p.response_time = time - p.arrival_time
                p.first_execution = False

            exec_time = min(tq,
                            p.remaining_burst_time)

            p.remaining_burst_time -= exec_time
            time += exec_time

            while remaining and remaining[0].arrival_time <= time:
                ready.append(remaining.pop(0))

            if p.remaining_burst_time > 0:
                ready.append(p)
                context_switches += 1

            else:
                p.completion_time = time
                p.turnaround_time = time - p.arrival_time
                p.waiting_time = (
                        p.turnaround_time -
                        p.original_burst_time
                )
                completed.append(p)

        return completed, context_switches


# =====================================================
# AI-ADRR
# =====================================================

class AI_ADRRScheduler(ADRRScheduler):

    def calculate_quantum(self, queue):

        if len(queue) <= 1:
            return 4

        bursts = [p.predicted_burst_time for p in queue]

        diffs = [
            abs(bursts[i] - bursts[i+1])
            for i in range(len(bursts)-1)
        ]

        avg = sum(diffs) / len(diffs)

        if avg > 12:
            return 10
        elif avg > 6:
            return 8
        elif avg > 3:
            return 6
        return 4


# =====================================================
# METRICS
# =====================================================

def calculate_metrics(procs):

    n = len(procs)

    avg_wt = sum(p.waiting_time for p in procs) / n
    avg_tat = sum(p.turnaround_time for p in procs) / n
    avg_rt = sum(p.response_time for p in procs) / n

    total_burst = sum(p.original_burst_time for p in procs)
    total_time = max(p.completion_time for p in procs)

    cpu_util = (total_burst / total_time) * 100

    return avg_wt, avg_tat, avg_rt, cpu_util


# =====================================================
# RESULTS TABLE
# =====================================================

def print_results(rr, adrr, ai, rr_cs, adrr_cs, ai_cs):

    print("\n" + "="*75)
    print("RR vs ADRR vs AI-ADRR (REAL DATASET)")
    print("="*75)

    print(f"{'Metric':<25}{'RR':<15}{'ADRR':<15}{'AI-ADRR'}")
    print("-"*75)

    rows = [

        ("Avg Waiting Time", rr[0], adrr[0], ai[0]),
        ("Avg Turnaround Time", rr[1], adrr[1], ai[1]),
        ("Avg Response Time", rr[2], adrr[2], ai[2]),
        ("CPU Utilization", rr[3], adrr[3], ai[3]),
        ("Context Switches", rr_cs, adrr_cs, ai_cs)

    ]

    for r in rows:

        print(f"{r[0]:<25}{r[1]:<15.2f}{r[2]:<15.2f}{r[3]:.2f}")

    print("="*75)

import numpy as np

def print_dataset_stats(name, processes):

    bursts = [p.original_burst_time for p in processes]

    print("\n" + "="*60)
    print(name)
    print("="*60)

    print("Processes:", len(processes))
    print("Burst Mean:", round(np.mean(bursts),2))
    print("Burst Std Dev:", round(np.std(bursts),2))
    print("Burst Min:", min(bursts))
    print("Burst Max:", max(bursts))
# =====================================================
# MAIN
# =====================================================

def main():

    base_processes = load_processes_from_csv("final_50_process_dataset.csv")

    low = low_variance_dataset(base_processes)
    moderate = moderate_variance_dataset(base_processes)
    high = high_variance_dataset(base_processes)

    datasets = [
        ("LOW VARIANCE DATASET", low),
        ("MODERATE VARIANCE DATASET", moderate),
        ("HIGH VARIANCE DATASET", high)
    ]

    for name, processes in datasets:

        print_dataset_stats(name, processes)

        rr = RoundRobinScheduler()
        adrr = ADRRScheduler()
        ai = AI_ADRRScheduler()

        rr_done, rr_cs = rr.schedule(processes)
        adrr_done, adrr_cs = adrr.schedule(processes)
        ai_done, ai_cs = ai.schedule(processes)

        print_results(
            calculate_metrics(rr_done),
            calculate_metrics(adrr_done),
            calculate_metrics(ai_done),
            rr_cs,
            adrr_cs,
            ai_cs
        )


if __name__ == "__main__":
    main()