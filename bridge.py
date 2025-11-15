import pycba as cba
import numpy as np
import matplotlib.pyplot as plt
from beam_functions import BeamModel


# Beam definition & constants
L = [1200]             # 1200 mm
E = 4000e6           # N/mm²
I = 418352.24        # mm⁴
EI = E * I           # N·mm²
R = [-1, 0, -1, 0]    # supports at both ends (vertical restrained, rotations free)
print("Max moment (Nm):", beam.beam_results.vRes[0].M.max())
yBarmm = 41.43 #centroidal axis distance from bottom
totalHeightmm = 76.27
strengthTensionMPa = 30
strengthCompressionMPa = 6

beam = BeamModel(EI = EI)
beam.add_support(1200, "roller")




for loadN in range(135, 1000, 10):
    cvals = beam.analyze_train(loadN)
    
    print("cvals: ", cvals)
    
    #check yielding in compression & tension at max moment
    mMaxNmm = cvals["Mmax"]["val"]
    tensMaxMpa = mMaxNmm*yBarmm/I
    compMaxMpa = mMaxNmm*(totalHeightmm-yBarmm)/I
    
    if (tensMaxMpa > strengthTensionMPa):
        print("Failed under tension at car1 load of " + str(loadN) + " N.")
        break
    elif (compMaxMpa > strengthCompressionMPa):
        print("Failed under compression at car1 load of " + str(loadN) + " N.")
        break


beam.display()
    