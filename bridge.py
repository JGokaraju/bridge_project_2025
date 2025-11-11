import pycba as cba
import numpy as np
import matplotlib.pyplot as plt

# Beam definition
L = [1200]             # 1200 mm
E = 4000e6           # N/mm²
I = 418352.24        # mm⁴
EI = E * I           # N·mm²
R = [-1, 0, -1, 0]    # supports at both ends (vertical restrained, rotations free)
  
# Loads: six point loads 
# P’s in N, a’s in mm
LM = [
  [1, 2, 67.5, 172, 0],
  [1, 2, 67.5, 348, 0],
  [1, 2, 67.5, 512, 0],
  [1, 2, 67.5, 688, 0],
  [1, 2, 91.0, 852, 0],
  [1, 2, 91.0, 1028, 0]
]

beam = cba.BeamAnalysis(L, EI, R, LM)
beam.analyze(500)       # 500 points per span for better resolution
beam.plot_results()

print("Reactions (N):", beam.beam_results.R)
print("Max moment (Nm):", beam.beam_results.vRes[0].M.max())
print("Max shear (N):", beam.beam_results.vRes[0].V.max())