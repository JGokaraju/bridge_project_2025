import pycba as cba
import numpy as np
import matplotlib.pyplot as plt
from beam_functions import BeamModel


# Beam definition & constants
L = [1200]             # 1200 mm
E = 4000.           # N/mm²
I = 629372.       # mm⁴
EI = E * I           # N·mm²
R = [-1, 0, -1, 0]    # supports at both ends (vertical restrained, rotations free)


yBarmm = 81.5 #centroidal axis distance from bottom
totalHeightmm = 103.81
strengthTensionMPa = 30
strengthCompressionMPa = 6
strengthShearMPa = 4
strenghtGlueMPa = 2
Q = 8898 #mm^3
B = 80 #mm
QGlue = 7774 #mm^3
BGlue = 10 #mm

beam = BeamModel(EI = EI)
beam.add_support(1200, "roller")

def analyze_fos():
    cvals = beam.analyze_train(125)
    
    
    #check yielding in compression & tension at max moment
    MMaxNmm = cvals["Mmax"]["val"]
    tensMaxMpa = MMaxNmm*yBarmm/I
    compMaxMpa = MMaxNmm*(totalHeightmm-yBarmm)/I
    
    VMaxNmm = cvals["Vmax"]["val"]
    tauMaxMPa = VMaxNmm*Q/I/B
    tauGlueMaxMPa = VMaxNmm*QGlue/I/BGlue
    
    
    return (strengthTensionMPa/tensMaxMpa,
            strengthCompressionMPa/compMaxMpa,
            strengthShearMPa/tauMaxMPa,
            strenghtGlueMPa/tauGlueMaxMPa)

print(analyze_fos())

def analyze_max_P():
    for loadN in range(135, 1000, 10):
        cvals = beam.analyze_train(loadN)
        
        
        #check yielding in compression & tension at max moment
        MMaxNmm = cvals["Mmax"]["val"]
        tensMaxMpa = MMaxNmm*yBarmm/I
        compMaxMpa = MMaxNmm*(totalHeightmm-yBarmm)/I
        
        VMaxNmm = cvals["Vmax"]["val"]
        tauMaxMPa = VMaxNmm*Q/I/B
        tauGlueMaxMPa = VMaxNmm*QGlue/I/BGlue
        
        
        if (tensMaxMpa > strengthTensionMPa):
            print("Failed under tension at car1 load of " + str(loadN) + " N.")
            break
        elif (compMaxMpa > strengthCompressionMPa):
            print("Failed under compression at car1 load of " + str(loadN) + " N.")
            break
        elif (tauMaxMPa > strengthShearMPa):
            print("Failed under shear at car1 load of " + str(loadN) + " N.")
            break
        elif (tauGlueMaxMPa > strenghtGlueMPa):
            print("Failed under glue shear at car1 load of " + str(loadN) + " N.")
            break



analyze_max_P()

beam.display()