"""Utilities for reading and harmonizing Oura API exports.

This module loads per-day Oura JSON files and returns a dictionary of summary
metrics and time-indexed signals in a consistent timezone.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import json


ACTIVITY_CLASS_DESCRIPTION = (
    "0 - not wear, 1 - rest, 2- inactive, 3- low activity, "
    "4 - medium activity, 5 - high activity"
)
SLEEP_PHASE_DESCRIPTION = "1 - deep sleep, 2 - light sleep, 3 - rem sleep, 4 - awake"


def concat_timeindexed(
    dfs: list[pd.DataFrame],
    output_tz: str = "America/Chicago",
    naive_input_tz: str = "UTC",
) -> pd.DataFrame:
    """Concatenate time-indexed DataFrames after timezone normalization.

    Args:
        dfs: Input DataFrames with DatetimeIndex-like index values.
        output_tz: Target timezone for the output index.
        naive_input_tz: Timezone assumed for naive timestamps before conversion.

    Returns:
        A concatenated DataFrame sorted by index and localized to ``output_tz``.
    """
    normalized = []
    for df in dfs:
        if df is None or len(df) == 0:
            continue
        dfi = df.copy()
        idx = pd.to_datetime(dfi.index)
        if idx.tz is None:
            idx = idx.tz_localize(naive_input_tz)
        dfi.index = idx.tz_convert(output_tz)
        normalized.append(dfi)

    if not normalized:
        return pd.DataFrame()
    return pd.concat(normalized).sort_index()


def load_json_records(path: str) -> list[dict] | None:
    """Load a JSON array from disk if the file exists.

    Args:
        path: Full path to the JSON file.

    Returns:
        Parsed list of records when present; otherwise ``None``.
    """
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

class OuraSubject:
    """Reader for a single subject's Oura export directory.

    Data schema reference: https://cloud.ouraring.com/v2/docs
    """

    def __init__(self, path_oura: str):
        """Initialize with the root Oura folder containing daily subfolders.

        Args:
            path_oura: Path whose children are date folders in YYYY-MM-DD format.
        """

        self.oura_path = path_oura
        self.oura_dates = sorted(os.listdir(path_oura))

    def get_oura_scores(self, date: datetime.date):
        """Load Oura features and time series for one date.

        Time-indexed outputs are converted to America/Chicago timezone.

        Activity class encoding used in ``act_5min``:
        0 - not wear, 1 - rest, 2- inactive, 3- low activity, 4 - medium activity, 5 - high activity

        Sleep phase encoding used in ``sleep_phases``:
        1 - deep sleep, 2 - light sleep, 3 - rem sleep, 4 - awake

        Args:
            date: Date to load.

        Returns:
            Dictionary with scalar daily metrics and DataFrames for time series,
            or ``None`` when non-wear is detected for the full day.

        Raises:
            ValueError: If no Oura data folder exists for ``date``.
        """
        scores = {}

        date_str = date.strftime("%Y-%m-%d")
        if date_str not in self.oura_dates:
            raise ValueError(f"No Oura data for date {date_str}")

        date_path = os.path.join(self.oura_path, date_str)

        dat = load_json_records(os.path.join(date_path, "heartrate.json"))
        if dat is not None:
            l_bpm = []
            for idx in range(len(dat)):
                if "data" in dat[idx] and dat[idx]["data"] is not None:
                    l_bpm.append(pd.DataFrame(dat[idx]["data"]))
            if len(l_bpm) > 0:
                scores["bpm"] = pd.concat(l_bpm, ignore_index=True)


        dat = load_json_records(os.path.join(date_path, "daily_activity.json"))
        if dat is not None:
            l_mets = []
            l_act_5min = []
            for idx in range(len(dat)):
                mets = dat[idx]["met"]["items"]
                start_time = dat[idx]["met"]["timestamp"]

                interval = dat[idx]["met"]["interval"]   # interval is 90s
                scores["active_calories"] = dat[idx]["active_calories"]
                scores["average_met_minutes"] = dat[idx]["average_met_minutes"]
                scores["equivalent_walking_distance"] = dat[idx]["equivalent_walking_distance"]
                scores["steps"] = dat[idx]["steps"]
                scores["resting_time"] = dat[idx]["resting_time"]
                scores["total_calories"] = dat[idx]["total_calories"]
                scores["medium_activity_time"] = dat[idx]["medium_activity_time"]
                scores["medium_activity_met_minutes"] = dat[idx]["medium_activity_met_minutes"]
                scores["score"] = dat[idx]["score"]
                scores["sedentary_time"] = dat[idx]["sedentary_time"]

                timestamps = pd.date_range(start=start_time, periods=len(mets), freq=f"{str(interval)}s")
                l_mets.append(pd.DataFrame(mets, index=timestamps, columns=["met"]))

                act_5min = np.array(list(dat[idx]["class_5_min"]), dtype=int)
                timestamp = dat[idx]["timestamp"]
                timestamps_5min = pd.date_range(start=timestamp, periods=len(act_5min), freq="5min")
                l_act_5min.append(pd.DataFrame(act_5min, index=timestamps_5min, columns=["class_5_min"]))

            if len(l_mets) > 0:
                scores["mets"] = concat_timeindexed(l_mets)
                if scores["mets"]["met"].nunique() == 1 and dat[-1]["non_wear_time"] == 86400:
                    print(f"Patient did not wear the Oura ring on {date_str}")
                    return None

            if len(l_act_5min) > 0:
                scores["act_5min"] = concat_timeindexed(l_act_5min)

        dat = load_json_records(os.path.join(date_path, "sleep.json"))
        if dat is not None:
            l_heart_rate = []
            l_hrv = []
            l_sleep_phases = []
            for idx in range(len(dat)):
                if dat[idx]["heart_rate"] is not None:
                    interval_s = dat[idx]["heart_rate"]["interval"]  # usually every 5 min. 300 sec
                    heart_rate = dat[idx]["heart_rate"]["items"]
                    start_time_s = dat[idx]["heart_rate"]["timestamp"]
                    timestamps_s = pd.date_range(start=start_time_s, periods=len(heart_rate), freq=f"{str(interval_s)}s")
                    l_heart_rate.append(pd.DataFrame(heart_rate, index=timestamps_s, columns=["heart_rate"]))

                if dat[idx]["hrv"] is not None:
                    interval_s = dat[idx]["hrv"]["interval"] # usually every 5 min. 300 sec
                    hrv = dat[idx]["hrv"]["items"]
                    start_time_s = dat[idx]["hrv"]["timestamp"]
                    timestamps_s = pd.date_range(start=start_time_s, periods=len(hrv), freq=f"{str(interval_s)}s")
                    l_hrv.append(pd.DataFrame(hrv, index=timestamps_s, columns=["hrv"]))

                bedtime_start = dat[idx]["bedtime_start"]
                sleepphases = np.array(list(dat[idx]["sleep_phase_5_min"]), dtype=int)
                timestamps_sleep = pd.date_range(start=bedtime_start, periods=len(sleepphases), freq="5min")

                l_sleep_phases.append(pd.DataFrame(sleepphases, index=timestamps_sleep, columns=["sleep_phase_5_min"]))
            if len(l_heart_rate) > 0:
                scores["sleep_heart_rate"] = concat_timeindexed(l_heart_rate)
            if len(l_hrv) > 0:
                scores["sleep_hrv"] = concat_timeindexed(l_hrv)
            if len(l_sleep_phases) > 0:
                scores["sleep_phases"] = concat_timeindexed(l_sleep_phases)
                

        dat = load_json_records(os.path.join(date_path, "daily_readiness.json"))
        if dat is not None:
            for idx in range(len(dat)):
                scores["temperature_deviation"] = dat[idx]["temperature_deviation"]
                scores["temperature_trend_deviation"] = dat[idx]["temperature_trend_deviation"]
                scores["score"] = dat[idx]["score"]

        dat = load_json_records(os.path.join(date_path, "daily_spo2.json"))
        if dat is not None:
            for idx in range(len(dat)):
                if dat[idx]["spo2_percentage"] is not None:
                    scores["spo2_percentage"] = dat[idx]["spo2_percentage"]["average"]
                if dat[idx]["breathing_disturbance_index"] is not None:
                    scores["breathing_disturbance_index"] = dat[idx]["breathing_disturbance_index"]
            # Breathing Disturbance Index (BDI) calculated using detected SpO2 drops from timeseries. Values should be in range [0, 100]

        dat = load_json_records(os.path.join(date_path, "daily_stress.json"))
        if dat is not None:
            for idx in range(len(dat)):
                scores["stress_high"] = dat[idx]["stress_high"] # Time (in seconds) spent in a high stress zone (top quartile data)
                scores["recovery_high"] = dat[idx]["recovery_high"] # Time (in seconds) spent in a high recovery zone (bottom quartile data)
                scores["day_summary"] = dat[idx]["day_summary"] # "restored" "normal" "stressful"

        return scores
    
if __name__ == "__main__":

    path_oura = "/mnt/datalake/data/TRBD-53761/TRBD001/oura"
    oura_subject = OuraSubject(path_oura)
    scores = oura_subject.get_oura_scores(datetime.strptime("2026-02-19", "%Y-%m-%d").date())