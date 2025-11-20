
import pycba as cba
import numpy as np
import matplotlib.pyplot as plt
from beam_functions import BeamModel


# Beam definition & constants
L = [300, 600, 300]            # length of each span (sums to 1200mm)
E = 4000e6           # N/mm²
I = np.array([418300, 418352.24, 418300])       # mm⁴
EI = E * I          # N·mm²
R = [-1, 0, -1, 0]    # supports at both ends (vertical restrained, rotations free)
yBarmm = [41.43, 41, 41]   #centroidal axis distance from bottom
height = [76.27, 76, 76]
strengthTensionMPa = 30
strengthCompressionMPa = 6
beam = BeamModel(EI = EI)


for i in range(len(L)):
    if i == len(L)-1:
        beam.add_support(L[i], "roller")
    else:
        beam.add_support(L[i], "filler")


spans = []
total = 0
for length in L:
    total += length
    spans.append(total)



for loadN in range(135, 1000, 10):
    failure_mode = "Span 1"
    cvals = beam.analyze_train(loadN)
    
   
    #check yielding in compression & tension at max moment
    mMaxNmm = cvals["Mmax"]["val"]

    at = cvals["Mmax"]["at"]
    if 0 <= at < spans[0]:
        I_span = I[0]
        mid_y = yBarmm[0]
        height_at_span = height[0]

    elif spans[0] <= at < spans[1]:
        I_span = I[1]
        mid_y = yBarmm[1]
        height_at_span = height[1]


    elif spans[1] <= at < spans[2]:
        I_span = I[2]
        mid_y = yBarmm[2]
        height_at_span = height[2]



    tensMaxMpa = {}
    compMaxMpa = {}
    tensMaxMpa["moment-designed span"] = mMaxNmm*mid_y/I_span
    compMaxMpa["moment-designed span"] = mMaxNmm*(height_at_span-mid_y)/I_span

    #Hard-Coded Case-by-Case Conditions
    moment_at_division, shear_at_division = beam.at_spans(spans[0])
    tensMaxMpa["shear-designed span"] = moment_at_division*yBarmm[0]/I[0]

    compMaxMpa["shear-designed span"] = moment_at_division*(height[0]-yBarmm[0])/I[0]

    MAX_TENSION = max(tensMaxMpa.values())
    MAX_COMPRESSION = max(compMaxMpa.values())

    print(MAX_COMPRESSION, MAX_TENSION, "c and t")

    if (MAX_TENSION > strengthTensionMPa):
        print("Failed under tension at car1 load of " + str(loadN) + " N.")
        result = [key for key, value in tensMaxMpa.items() if value == MAX_TENSION]
        print(f"Failed at the {result}")

        break
    elif (MAX_COMPRESSION > strengthCompressionMPa):
        print("Failed under compression at car1 load of " + str(loadN) + " N.")

        result = [key for key, value in compMaxMpa.items() if value == MAX_COMPRESSION]
        print(f"Failed at the {result}")
        break

pos = cvals["Mmax"]["pos"][0]
at = cvals["Mmax"]["at"]
val = cvals["Mmax"]["val"]
print(f"Max moment is {val} kNm at {at:.2f} m when front axle position is {pos} m")

beam.display()    

