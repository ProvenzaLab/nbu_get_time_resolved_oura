import pandas as pd
import numpy as np
import json
import os
from matplotlib import pyplot as plt

# https://cloud.ouraring.com/v2/docs
path_ = "/mnt/datalake/data/TRBD-53761/TRBD002/oura"

dates = os.listdir(path_)
date = dates[16]

with open(os.path.join(path_, date, "heartrate.json"), "r") as f:
    dat = json.load(f)
    bpm = pd.DataFrame(dat[0]["data"])

with open(os.path.join(path_, date, "daily_activity.json"), "r") as f:
    dat = json.load(f)
    mets = dat[0]["met"]["items"]
    start_time = dat[0]["met"]["timestamp"]
    # interval is 90s
    interval = dat[0]["met"]["interval"]
    active_calories = dat[0]["active_calories"]
    average_met_minutes = dat[0]["average_met_minutes"]
    equivalent_walking_distance = dat[0]["equivalent_walking_distance"]
    steps = dat[0]["steps"]
    resting_time = dat[0]["resting_time"]
    total_calories = dat[0]["total_calories"]
    medium_activity_time = dat[0]["medium_activity_time"]
    medium_activity_met_minutes = dat[0]["medium_activity_met_minutes"]
    score = dat[0]["score"]
    sedentary_time = dat[0]["sedentary_time"]

    timestamps = pd.date_range(start=start_time, periods=len(mets), freq=f"{str(interval)}s")
    mets = pd.DataFrame(mets, index=timestamps)

    act_5min = np.array(list(dat[0]["class_5_min"]), dtype=int)
    timestamp = dat[0]["timestamp"]
    timestamps_5min = pd.date_range(start=timestamp, periods=len(act_5min), freq="5min")
    act_5min = pd.DataFrame(act_5min, index=timestamps_5min, columns=["class_5_min"])
    # 0 - not wear, 1 - rest, 2- inactive, 3- low activity, 4 - medium activity, 5 - high activity

with open(os.path.join(path_, date, "sleep.json"), "r") as f:
    dat = json.load(f)
    interval_s = dat[0]["heart_rate"]["interval"]
    heart_rate = dat[0]["heart_rate"]["items"]
    start_time_s = dat[0]["heart_rate"]["timestamp"]
    timestamps_s = pd.date_range(start=start_time_s, periods=len(heart_rate), freq=f"{str(interval_s)}S")
    heart_rate = pd.DataFrame(heart_rate, index=timestamps_s, columns=["heart_rate"])

    # repeat the same for hrv
    interval_s = dat[0]["hrv"]["interval"]
    hrv = dat[0]["hrv"]["items"]
    start_time_s = dat[0]["hrv"]["timestamp"]
    timestamps_s = pd.date_range(start=start_time_s, periods=len(hrv), freq=f"{str(interval_s)}S")
    hrv = pd.DataFrame(hrv, index=timestamps_s, columns=["hrv"])

    bedtime_start = dat[0]["bedtime_start"]
    sleepphases = np.array(list(dat[0]["sleep_phase_5_min"]), dtype=int)
    timestamps_sleep = pd.date_range(start=bedtime_start, periods=len(sleepphases), freq="5T")
    sleepphases = pd.DataFrame(sleepphases, index=timestamps_sleep, columns=["sleep_phase_5_min"])
    # 1 - deep sleep, 2 - light sleep, 3 - rem sleep, 4 - awake

with open(os.path.join(path_, date, "daily_readiness.json"), "r") as f:
    dat = json.load(f)
    temperature_deviation = dat[0]["temperature_deviation"]
    temperature_trend_deviation = dat[0]["temperature_trend_deviation"]
    score = dat[0]["score"]

#with open(os.path.join(path_, date, "daily_resilience.json"), "r") as f:
#    dat = json.load(f)

with open(os.path.join(path_, date, "daily_spo2.json"), "r") as f:
    dat = json.load(f)
    spo2_percentage = dat[0]["spo2_percentage"]["average"]
    breathing_disturbance_index = dat[0]["breathing_disturbance_index"]
    # Breathing Disturbance Index (BDI) calculated using detected SpO2 drops from timeseries. Values should be in range [0, 100]

with open(os.path.join(path_, date, "daily_stress.json"), "r") as f:
    dat = json.load(f)
    stress_high = dat[0]["stress_high"] # Time (in seconds) spent in a high stress zone (top quartile data)
    stress_recoveryhigh = dat[0]["recovery_high"] # Time (in seconds) spent in a high recovery zone (bottom quartile data)
    stress_daysummary = dat[0]["day_summary"] # "restored" "normal" "stressful"

    timestamps_readiness = pd.date_range(start=timestamp, periods=len(readiness), freq="D")
    readiness = pd.DataFrame(readiness, index=timestamps_readiness, columns=["readiness_score"])






plt.figure(figsize=(10, 3))
plt.plot(mets.index, mets[0], marker="o", linestyle="None")
plt.xlabel("Time")
plt.ylabel("METs")
plt.title("METs Over Time")
plt.savefig("mets_plot.png")
df["timestamp"] = pd.to_datetime(df["timestamp"])
plt.figure(figsize=(10, 3))
plt.plot(df["timestamp"], df["bpm"], marker="o", linestyle="None")
plt.xlabel("Time")
plt.ylabel("Heart Rate (bpm)")
plt.title("Heart Rate Over Time")
plt.savefig("heart_rate_plot.png")

# plot the time series as a function of index
plt.figure(figsize=(10, 5))
plt.plot(df.index, df["timestamp"], marker="o", linestyle="None")
plt.xlabel("Index")
plt.ylabel("Timestamp")
plt.title("Heart Rate Over Time (Index)")
plt.tight_layout()
plt.savefig("heart_rate_plot_index.png")