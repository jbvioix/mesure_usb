#!/usr/bin/python3
# -*- coding: utf-8 -*-

import visa
import time
import numpy as np
import csv

import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use('fivethirtyeight')
from matplotlib import cm
plt.rcParams["font.sans-serif"] = "Raleway"

FREQ_MIN=2 #puissance de 10
FREQ_MAX=5 #puissance de 10
NB=60
FICHIER="MesuresFiltre.csv"


rm = visa.ResourceManager('@py')
instruments = rm.list_resources()

# Recherche des instruments
for _ in instruments:
    if 'DS' in _:
        oscilloscope_ = _
        print("Oscilloscope :", end=" ")
        oscilloscope = rm.open_resource(oscilloscope_)
        print(oscilloscope.query("*IDN?"))
    if 'DG' in _:
        generator_ = _
        print("Générateur :", end=" ")
        generator = rm.open_resource(generator_)
        print(generator.query("*IDN?"))

# Reset des instruments
generator.query("*RST")
oscilloscope.query("*RST")
time.sleep(5)
# Parcours d'une bande de fréquences
results = np.zeros((NB, 5))
generator.query("OUTP ON")
for idx, f in enumerate(np.logspace(FREQ_MIN, FREQ_MAX, NB)):
    generator.query("APPL:SIN %f,1.0,0.0" % (f,))
    oscilloscope.query(":AUTO")

    time.sleep(5) # Nécessaire pour que l'auto-set se fasse

    results[idx, 0] = float(oscilloscope.query(":MEAS:FREQ? CHAN1"))
    results[idx, 1] = float(oscilloscope.query(":MEAS:VRMS? CHAN1"))
    results[idx, 2] = float(oscilloscope.query(":MEAS:VRMS? CHAN2"))

    # Changement de la base de temps pour que l'oscillo soit plus précis...
    time_base = oscilloscope.query(":TIM:SCAL?")
    oscilloscope.query(":TIM:SCAL %f"%(float(time_base)/4.0))
    # Passage en mode AC...
    oscilloscope.query(":CHAN2:COUP AC")
    time.sleep(2)

    _ = oscilloscope.query(":MEAS:PDEL? CHAN2")
    results[idx, 3] = 0.0 if (("<" or ">") in _ ) else float(_)
    _ = oscilloscope.query(":MEAS:NDEL? CHAN2")
    results[idx, 4] = 0.0 if (("<" or ">") in _ ) else float(_)

# Sauvegarde des données en CSV
with open(FICHIER, "w") as f:
    writer = csv.writer(f, delimiter=',')
    writer.writerow(["#Freq. (Hz)", "In (Vrms)", "Out (Vrms)", "Pdel", "Ndel"])
    writer.writerows(results)

# Affichage du gain en fonction de la fréquencels
gain = 20 * np.log10(results[:, 2] / results[:, 1])
plt.figure(figsize=(15, 10))
plt.semilogx(results[:, 0], gain, '-o')
plt.grid(True, 'minor')
plt.grid(True, 'major')
plt.ylim( (np.min(gain)-2.0, np.max(gain)+2.0) )
plt.ylabel('Amplitude [dB]')
plt.xlabel(u'Fréquence [Hz]')
plt.title("Diagramme de Bode du filtre")
plt.show()
