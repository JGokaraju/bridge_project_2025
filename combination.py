import numpy as np
import pycba as cba
import matplotlib.pyplot as plt
from beam_functions import BeamModel


beam_type = "nonuniform"    # or "uniform"


# DEFINE PARAMETERS

uniform_params = dict(
    L=[1200],
    E=4000.,                   # N/mm²
    I=629372.,                 # mm⁴
    ybar=81.5,
    height=103.81,
    Q=8898,
    B=80,
    Q_glue=7774,
    B_glue=10,
    strength_tension=30,
    strength_compression=6,
    strength_shear=4,
    strength_glue=2
)


nonuniform_params = dict(
    L=[300, 600, 300],
    E=4000,                    # N/mm²
    I=np.array([929372, 629372, 929372]),
    ybar=[81, 81, 81],
    height=[103, 103, 103],

    # constant for entire beam
    Q=[8988, 8988, 8988], #Place the Largest Value of Q here, not just at the centroid
    B=[80, 80, 80],
    Q_glue=[7774, 7774, 7774],
    B_glue=[10, 10, 10],

    strength_tension=30,
    strength_compression=6,
    strength_shear=4,
    strength_glue=2
)


# HELPER FUNCTIONS

def build_beam(params):
    ''' Call to Construct Beam Based on Given Parameters'''
    EI = params["E"] * params["I"]
    beam = BeamModel(EI=EI)

    # Add supports
    L = params["L"]
    for i in range(len(L)):
        if i == len(L) - 1:
            beam.add_support(L[i], "roller")
        else:
            beam.add_support(L[i], "filler")
    return beam


def find_span(at, spans):
    ''' Identify Span Location. Pass in position and spans'''
    for i, s in enumerate(spans):
        if at < s:
            return i
    return len(spans) - 1


# ============================================================
# UNIFORM FOS
# ============================================================

def analyze_uniform_fos(params, beam):
    cvals = beam.analyze_train(100)

    M = cvals["Mmax"]["val"]
    V = cvals["Vmax"]["val"]

    I = params["I"]
    y = params["ybar"]
    h = params["height"]

    return (
        params["strength_tension"] / (M * y / I),
        params["strength_compression"] / (M * (h - y) / I),
        params["strength_shear"] / (V * params["Q"] / (I * params["B"])),
        params["strength_glue"] / (V * params["Q_glue"] / (I * params["B_glue"]))
    )


# ============================================================
# UNIFORM MAX P
# ============================================================

def analyze_uniform_maxP(params, beam):
    for load in range(135, 2000, 10):

        c = beam.analyze_train(load)
        M = c["Mmax"]["val"]
        V = c["Vmax"]["val"]
        

        I = params["I"]
        y = params["ybar"]
        h = params["height"]

        tens = M * y / I
        comp = M * (h - y) / I
        shear = V * params["Q"] / (I * params["B"])
        glue = V * params["Q_glue"] / (I * params["B_glue"])
        print(glue)

        if tens > params["strength_tension"]:
            print(f"FAILED tension at P={load} N")
            break
        if comp > params["strength_compression"]:
            print(f"FAILED compression at P={load} N")
            break
        if shear > params["strength_shear"]:
            print(f"FAILED shear at P={load} N")
            break
        if glue > params["strength_glue"]:
            print(f"FAILED glue shear at P={load} N")
            break

    beam.display()


# ============================================================
# NONUNIFORM MAX P  (now includes shear + glue too)
# ============================================================

def analyze_nonuniform_maxP(params, beam):

    spans = np.cumsum(params["L"])

    for load in range(135, 2000, 10):

        c = beam.analyze_train(load)

        tensMaxMpa = {}
        compMaxMpa = {}
        shearPlateMax = {}
        shearGlueMax = {}

        target_Moment_y_1, target_Shear_y_1 = beam.at_spans(spans[0])
        target_Moment_y_2, target_Shear_y_2 = beam.at_spans(0)
        target_Moment_y_3, target_Shear_y_3 = beam.at_spans(1200)
        target_Moment_y_4, target_Shear_y_4 = beam.at_spans(spans[1])
        maxMoment = max(target_Moment_y_1, target_Moment_y_2, target_Moment_y_3, target_Moment_y_4)
        maxShear = max(target_Shear_y_1, target_Shear_y_2, target_Shear_y_3, target_Shear_y_4)
        print(f"The Max Moment Relevant for the First Span is {maxMoment}")
        print(f"The Max Shear Relevant for the First Span is {maxShear}")

        #Providing Relevant Features for the Seperate Spans
        I_support_span = params["I"][0]
        y_support_span = params["ybar"][0]
        h_support_span = params["height"][0]
        tensMaxMpa["shear-designed span"] =  maxMoment * y_support_span / I_support_span
        compMaxMpa["shear-designed span"] = maxMoment * (h_support_span - y_support_span) / I_support_span

        shearPlateMax["shear-designed span"] = maxShear * params["Q"][0] / (I_support_span * params["B"][0])
        shearGlueMax["shear-designed span"] = maxShear * params["Q_glue"][0] / (I_support_span * params["B_glue"][0])

        #It is known max Moment always occurs in the central span, so this is hard-coded.
        M_central_Span = c["Mmax"]["val"]
        V_central_span = max(target_Shear_y_1, target_Shear_y_4)
        print(f"The Max Shear Relevant for the Central Span is {V_central_span}")
        print(f"The Max Moment Relevant for the Central Span is {M_central_Span}")


        
        # Define Parameters for that Span
        I = params["I"][1]
        y = params["ybar"][1]
        h = params["height"][1]

        # bending stresses
        tensMaxMpa["moment-designed span"] =  M_central_Span * y / I
        compMaxMpa["moment-designed span"] = M_central_Span * (h - y) / I

        # shear stresses (constants)
        shearPlateMax["moment-designed span"] = V_central_span * params["Q"][1] / (I * params["B"][1])
        shearGlueMax["moment-designed span"] = V_central_span * params["Q_glue"][1] / (I * params["B_glue"][1])

        tens = max(tensMaxMpa.values())
        comp = max(compMaxMpa.values())
        shear = max(shearPlateMax.values())
        glue = max(shearGlueMax.values())


        if tens > params["strength_tension"]:
            print(f"FAILED tension at P={load} N)")
            result = [key for key, value in tensMaxMpa.items() if value == tens]
            print(f"Failed at the {result}")
            break
        if comp > params["strength_compression"]:
            print(compMaxMpa.items())
            print(f"FAILED compression at P={load} N)")
            result = [key for key, value in compMaxMpa.items() if value == comp]
            print(f"Failed at the {result}")
            break
        if shear > params["strength_shear"]:
            print(f"FAILED shear at P={load} N ")
            result = [key for key, value in shearPlateMax.items() if value == shear]
            print(f"Failed at the {result}")
            break
        if glue > params["strength_glue"]:
            print(f"FAILED glue shear at P={load} N")
            result = [key for key, value in shearGlueMax.items() if value == glue]
            print(f"Failed at the {result}")
            break

    beam.display()


# ============================================================
# RUN THE CHOSEN ANALYSIS
# ============================================================

if beam_type == "uniform":
    params = uniform_params
    beam = build_beam(params)
    print("FoS =", analyze_uniform_fos(params, beam))
    analyze_uniform_maxP(params, beam)

else:
    params = nonuniform_params
    beam = build_beam(params)
    analyze_nonuniform_maxP(params, beam)
