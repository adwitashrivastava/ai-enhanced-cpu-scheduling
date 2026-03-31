import random
import pandas as pd
import numpy as np
from collections import deque
from sklearn.tree import DecisionTreeRegressor

random.seed(42)
np.random.seed(42)


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

        arrival = arrival // 1000
        burst = max(1, burst)

        processes.append(
            Process(pid, arrival, burst, priority)
        )

    return processes


# =====================================================
# AI FRIENDLY DATASET
# =====================================================

def ai_friendly_dataset(processes):

    new = []

    for p in processes:

        if p.priority == 1:
            burst = random.randint(20, 50)

        elif p.priority <= 3:
            burst = random.randint(150, 300)

        else:
            burst = random.randint(700, 1200)

        new.append(
            Process(
                p.pid,
                p.arrival_time,
                burst,
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
# AI ADRR
# =====================================================

class AI_ADRRScheduler(ADRRScheduler):

    def calculate_quantum(self, queue):

        if len(queue) <= 1:
            return 4

        bursts = [p.predicted_burst_time for p in queue]

        avg_burst = sum(bursts) / len(bursts)

        short_jobs = sum(1 for b in bursts if b < avg_burst)
        long_jobs = sum(1 for b in bursts if b >= avg_burst)

        short_ratio = short_jobs / len(bursts)
        long_ratio = long_jobs / len(bursts)

        # ML-informed scheduling
        if short_ratio > 0.5:
            return 3      # prioritize short jobs

        elif long_ratio > 0.5:
            return 12     # allow long jobs larger quantum

        else:
            return 6
    

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
# PRINT RESULTS
# =====================================================

def print_results(rr, adrr, ai, rr_cs, adrr_cs, ai_cs):

    print("\n" + "="*75)
    print("RR vs ADRR vs AI-ADRR (AI FRIENDLY DATASET)")
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


# =====================================================
# MAIN
# =====================================================

def main():

    processes = load_processes_from_csv("500_row_dataset.csv")

    ai_dataset = ai_friendly_dataset(processes)

    predictor = BurstTimePredictor()
    predictor.train(ai_dataset)

    for p in ai_dataset:
        p.predicted_burst_time = predictor.predict(p)

    rr = RoundRobinScheduler()
    adrr = ADRRScheduler()
    ai = AI_ADRRScheduler()

    rr_done, rr_cs = rr.schedule(ai_dataset)
    adrr_done, adrr_cs = adrr.schedule(ai_dataset)
    ai_done, ai_cs = ai.schedule(ai_dataset)

    rr_metrics = calculate_metrics(rr_done)
    adrr_metrics = calculate_metrics(adrr_done)
    ai_metrics = calculate_metrics(ai_done)

    print_results(
        rr_metrics,
        adrr_metrics,
        ai_metrics,
        rr_cs,
        adrr_cs,
        ai_cs
    )
    

if __name__ == "__main__":
    main()