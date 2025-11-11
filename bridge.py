import pycba as cba
import numpy as np
import matplotlib.pyplot as plt

# Beam definition
L = [1.2]             # 1200 mm = 1.2 m
EI = 1673.4           # kN·m² (E = 4000 MPa, I = 418352.24 mm⁴)
R = [-1, 0, -1, 0]    # supports at both ends (vertical restrained, rotations free)
  
# Loads: six point loads 
# P’s in kN, a’s in m
LM = [
  [1, 2, 67.5, 0.172, 0],
  [1, 2, 67.5, 0.348, 0],
  [1, 2, 67.5, 0.512, 0],
  [1, 2, 67.5, 0.688, 0],
  [1, 2, 91.0, 0.852, 0],
  [1, 2, 91.0, 1.028, 0]
]

beam = cba.BeamAnalysis(L, EI, R, LM)
beam.analyze(500)       # 500 points per span for better resolution
beam.plot_results()

print("Reactions (kN):", beam.beam_results.R)
print("Max moment (kNm):", beam.beam_results.vRes[0].M.max())
print("Max shear (kN):", beam.beam_results.vRes[0].V.max())