import pickle
import os
from oura import OuraSubject
import sys

path_neural = "/mnt/labworlds/Provenza/lfp_timedomain_check/raw_timedomain/"

patients_ = [f for f in os.listdir(path_neural) if f.endswith(".pkl")]
res_dates = {}

for patient in patients_[::-1]:

    with open(os.path.join(path_neural, patient), "rb") as f:
        data = pickle.load(f)
    res_dates[patient] = {}
    # ok, was sollte die Idee sein
    # du hast unterschiedliche Dates für jedes Subject
    # ich würde für jedes Date (das ist) `times´ in Zeitzone Houston
    # die entsprechenden Oura scores rausziehen
    # das sollte einfach gehen
    # patient*innen haben nie einen workout in der NBU gemacht
    # data is a dataframe with a column "times" that contains timestamps in UTC
    unique_dates = data["times"].dt.date.unique()

    ouraSubject = OuraSubject(patient)

    for date in unique_dates:
        try:
            scores = ouraSubject.get_oura_scores(date)
            res_dates[patient][date] = scores
            print(f"Finished parsing Oura scores for {patient} on {date}")
        except ValueError as e:
            print(e)

with open(f"oura_scores.pkl", "wb") as f:
    pickle.dump(res_dates, f)

