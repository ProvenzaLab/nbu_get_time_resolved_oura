import pandas as pd
import numpy as np
import os
from datetime import datetime
import json

class OuraSubject:

    # https://cloud.ouraring.com/v2/docs

    def __init__(self, patient: str):
        if "TRB" in patient:
            path_oura = f"/mnt/datalake/data/TRBD-53761/{patient.split('_')[0]}/oura"
        elif "AA" in patient:
            path_oura = f"/mnt/datalake/data/AA-56119/{patient.split('_')[0]}/oura"
        elif "P0" in patient:
            path_oura = f"/mnt/datalake/data/PerceptOCD-48392/{patient.split('_')[0]}/oura"

        self.oura_path = path_oura
        self.patient = patient

        self.oura_dates = sorted(os.listdir(path_oura))

    def get_oura_scores(self, date: datetime.date):
        scores = {}

        date_str = date.strftime("%Y-%m-%d")
        if date_str not in self.oura_dates:
            raise ValueError(f"No Oura data for patient {self.patient} date {date_str}")

        date_path = os.path.join(self.oura_path, date_str)

        path_read = os.path.join(date_path, "heartrate.json")
        if os.path.exists(path_read):
            with open(path_read, "r") as f:
                dat = json.load(f)
                scores["bpm"] = pd.DataFrame(dat[0]["data"])


        path_read = os.path.join(date_path, "daily_activity.json")
        if os.path.exists(path_read):
            with open(path_read, "r") as f:
                dat = json.load(f)
                mets = dat[0]["met"]["items"]
                start_time = dat[0]["met"]["timestamp"]

                interval = dat[0]["met"]["interval"]   # interval is 90s
                scores["active_calories"] = dat[0]["active_calories"]
                scores["average_met_minutes"] = dat[0]["average_met_minutes"]
                scores["equivalent_walking_distance"] = dat[0]["equivalent_walking_distance"]
                scores["steps"] = dat[0]["steps"]
                scores["resting_time"] = dat[0]["resting_time"]
                scores["total_calories"] = dat[0]["total_calories"]
                scores["medium_activity_time"] = dat[0]["medium_activity_time"]
                scores["medium_activity_met_minutes"] = dat[0]["medium_activity_met_minutes"]
                scores["score"] = dat[0]["score"]
                scores["sedentary_time"] = dat[0]["sedentary_time"]

                timestamps = pd.date_range(start=start_time, periods=len(mets), freq=f"{str(interval)}s")
                scores["mets"] = pd.DataFrame(mets, index=timestamps, columns=["met"])
                if scores["mets"]["met"].nunique() == 1 and dat[0]["non_wear_time"] == 86400:
                    print(f"Patient {self.patient} did not wear the Oura ring on {date_str}")
                    return None

                act_5min = np.array(list(dat[0]["class_5_min"]), dtype=int)
                timestamp = dat[0]["timestamp"]
                timestamps_5min = pd.date_range(start=timestamp, periods=len(act_5min), freq="5min")
                scores["act_5min"] = pd.DataFrame(act_5min, index=timestamps_5min, columns=["class_5_min"])
                # 0 - not wear, 1 - rest, 2- inactive, 3- low activity, 4 - medium activity, 5 - high activity

        path_read = os.path.join(date_path, "sleep.json")
        if os.path.exists(path_read):
            with open(path_read, "r") as f:
                dat = json.load(f)
                if dat[0]["heart_rate"] is not None:
                    interval_s = dat[0]["heart_rate"]["interval"]  # usually every 5 min. 300 sec
                    heart_rate = dat[0]["heart_rate"]["items"]
                    start_time_s = dat[0]["heart_rate"]["timestamp"]
                    timestamps_s = pd.date_range(start=start_time_s, periods=len(heart_rate), freq=f"{str(interval_s)}S")
                    scores["sleep_heart_rate"] = pd.DataFrame(heart_rate, index=timestamps_s, columns=["heart_rate"])

                if dat[0]["hrv"] is not None:
                    interval_s = dat[0]["hrv"]["interval"] # usually every 5 min. 300 sec
                    hrv = dat[0]["hrv"]["items"]
                    start_time_s = dat[0]["hrv"]["timestamp"]
                    timestamps_s = pd.date_range(start=start_time_s, periods=len(hrv), freq=f"{str(interval_s)}S")
                    scores["sleep_hrv"] = pd.DataFrame(hrv, index=timestamps_s, columns=["hrv"])

                bedtime_start = dat[0]["bedtime_start"]
                sleepphases = np.array(list(dat[0]["sleep_phase_5_min"]), dtype=int)
                timestamps_sleep = pd.date_range(start=bedtime_start, periods=len(sleepphases), freq="5T")
                scores["sleep_phases"] = pd.DataFrame(sleepphases, index=timestamps_sleep, columns=["sleep_phase_5_min"])
                # 1 - deep sleep, 2 - light sleep, 3 - rem sleep, 4 - awake

        path_read = os.path.join(date_path, "daily_readiness.json")
        if os.path.exists(path_read):
            with open(path_read, "r") as f:
                dat = json.load(f)
                scores["temperature_deviation"] = dat[0]["temperature_deviation"]
                scores["temperature_trend_deviation"] = dat[0]["temperature_trend_deviation"]
                scores["score"] = dat[0]["score"]

        path_read = os.path.join(date_path, "daily_spo2.json")
        if os.path.exists(path_read):
            with open(path_read, "r") as f:
                dat = json.load(f)
                if dat[0]["spo2_percentage"] is not None:
                    scores["spo2_percentage"] = dat[0]["spo2_percentage"]["average"]
                if dat[0]["breathing_disturbance_index"] is not None:
                    scores["breathing_disturbance_index"] = dat[0]["breathing_disturbance_index"]
                # Breathing Disturbance Index (BDI) calculated using detected SpO2 drops from timeseries. Values should be in range [0, 100]

        path_read = os.path.join(date_path, "daily_stress.json")
        if os.path.exists(path_read):
            with open(path_read, "r") as f:
                dat = json.load(f)
                scores["stress_high"] = dat[0]["stress_high"] # Time (in seconds) spent in a high stress zone (top quartile data)
                scores["recovery_high"] = dat[0]["recovery_high"] # Time (in seconds) spent in a high recovery zone (bottom quartile data)
                scores["day_summary"] = dat[0]["day_summary"] # "restored" "normal" "stressful"

        return scores
    