# AI-Enhanced CPU Scheduling Research

## Overview
A research-based simulation comparing traditional Round Robin (RR), Adaptive Dynamic Round Robin (ADRR), and AI-Enhanced ADRR scheduling algorithms under varying workload conditions.

## Problem
Traditional CPU scheduling algorithms assume static workloads and use fixed time quantum values, leading to:
- High context switching
- Poor responsiveness
- Inefficient CPU utilization

## Solution
This research introduces an AI-enhanced scheduler that predicts burst times using machine learning to dynamically adjust scheduling decisions.

## Tech Stack
- Python
- Scikit-learn
- Decision Tree Regressor
- Simulation-based scheduling environment

## Algorithms Compared
- Round Robin (RR)
- Adaptive Dynamic Round Robin (ADRR)
- AI-Enhanced ADRR

## My Contribution
- Built Python simulation environment
- Implemented all scheduling algorithms
- Developed AI burst-time prediction model
- Generated workload datasets
- Conducted experimental analysis
- Evaluated performance metrics
- Wrote methodology and results sections

## Performance Metrics
- Waiting Time
- Turnaround Time
- Response Time
- CPU Utilization
- Context Switching

## Key Findings
- RR → Highest context switching
- ADRR → Lowest scheduling overhead
- AI-ADRR → Balanced performance with predictive optimization

## Research Focus
- Workload size impact
- Burst time variance
- Time quantum influence
- Process arrival patterns

## Future Work
- Reinforcement learning scheduler
- Real OS kernel integration
- Multi-core CPU scheduling support
