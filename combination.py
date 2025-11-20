import numpy as np
import pycba as cba
import matplotlib.pyplot as plt
from beam_functions import BeamModel
import math

beam_type = "nonuniform"    # or "uniform"


# DEFINE PARAMETERS

uniform_params = dict(
    L=[1200],
    E=4000.,                   # N/mm²
    I=294994.,                 # mm⁴
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
    strength_glue=2,

    mu=0.3,

    t1=[10, 12], 
    b1=[50, 50],
    t2=[8, 9],   
    b2=[30, 30],
    t3=[6, 7],   
    b3=[20, 20],
    t4=[5, 5],   
    h4=[40, 40], 
    a=[15, 15],

    y_plate=[
        [100, 50, 25],
        [120, 60, 30]
    ],

    Q_Flexural_Stress_Buckling=[8988, 8988],
    B_Flexural_Stress_Buckling=[80, 80],
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
    cvals = beam.analyze_train(135)

    M = cvals["Mmax"]["val"]
    V = cvals["Vmax"]["val"]

    print(beam.at_spans(350))

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

def optimize_split(params):
    prev = 10000
    best = 0
    for i in range(10, 400, 20):
        params["L"] = [i, 1200-2*i, i]

        new_val = analyze_fos_nonuniform(params)
        if new_val <= prev:
            best = i
    print(f"The optimal split is at {best} mm")
    

def analyze_fos_nonuniform(params):
    beam = build_beam(params)
    cvals = beam.analyze_train(100)

    spans = np.cumsum(params["L"])


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
    M_central_Span = cvals["Mmax"]["val"]
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

    FOS_c5 = []
    FOS_c6 = []
    FOS_c7 = []
    FOS_c8 = []

    denom = 12 * (1 - params["mu"]**2)
    
    span_1_sigma1 = (4 * math.pi**2 * params["E"] / denom) * (params["t1"][0] / params["b1"][0])**2
    span_1_sigma2 = (0.425 * math.pi**2 * params["E"] / denom) * (params["t2"][0] / params["b2"][0])**2
    span_1_sigma3 = (6 * math.pi**2 * params["E"] / denom) * (params["t3"][0] / params["b3"][0])**2
    span_1_tau    = (5 * math.pi**2 * params["E"] / denom) * ((params["t4"][0] / params["h4"][0])**2 + (params["t4"][0] / params["a"][0])**2)

    span_1_flange = maxMoment * params["y_plate"][0][0]/ I_support_span
    span_1_tips = maxMoment * params["y_plate"][0][1]/ I_support_span
    span_1_web = maxMoment * params["y_plate"][0][2]/ I_support_span
    span_1_flexural = maxShear * params["Q Flexural Stress Buckling"][0] / (I_support_span * params["B Flexural Stess Buckling"][0])

    FOS_c5.append(span_1_sigma1/span_1_flange)
    FOS_c6.append(span_1_sigma2/span_1_tips)
    FOS_c7.append(span_1_sigma3/span_1_web)
    FOS_c8.append(span_1_tau/span_1_flexural)

    span_2_sigma1 = (4 * math.pi**2 * params["E"] / denom) * (params["t1"][1] / params["b1"][1])**2
    span_2_sigma2 = (0.425 * math.pi**2 * params["E"] / denom) * (params["t2"][1] / params["b2"][1])**2
    span_2_sigma3 = (6 * math.pi**2 * params["E"] / denom) * (params["t3"][1] / params["b3"][1])**2
    span_2_tau    = (5 * math.pi**2 * params["E"] / denom) * ((params["t4"][1] / params["h4"][1])**2 + (params["t4"][1] / params["a"][1])**2)

    span_2_flange = maxMoment * params["y_plate"][1][0]/ I_support_span
    span_2_tips = maxMoment * params["y_plate"][1][1]/ I_support_span
    span_2_web = maxMoment * params["y_plate"][1][2]/ I_support_span
    span_2_flexural = maxShear * params["Q Flexural Stress Buckling"][1] / (I_support_span * params["B Flexural Stess Buckling"][1])

    FOS_c5.append(span_2_sigma1/span_2_flange)
    FOS_c6.append(span_2_sigma2/span_2_tips)
    FOS_c7.append(span_2_sigma3/span_2_web)
    FOS_c8.append(span_2_tau/span_2_flexural)

    FOS_c5, FOS_c6, FOS_c7, FOS_c8 = [], [], [], []

    denom = 12 * (1 - params["mu"]**2)
    E = params["E"]
    for i in range(len(params["t1"])):

        # --- Buckling stresses ---
        sigma1 = sigma_buckling(4,     params["t1"][i], params["b1"][i], E, denom)
        sigma2 = sigma_buckling(0.425, params["t2"][i], params["b2"][i], E, denom)
        sigma3 = sigma_buckling(6,     params["t3"][i], params["b3"][i], E, denom)
        tau    = tau_buckling(params["t4"][i], params["h4"][i], params["a"][i], E, denom)

        # --- Applied stresses ---
        flange_stress   = maxMoment * params["y_plate"][i][0] / I_support_span
        tips_stress     = maxMoment * params["y_plate"][i][1] / I_support_span
        web_stress      = maxMoment * params["y_plate"][i][2] / I_support_span
        flexural_stress = (maxShear * params["Q Flexural Stress Buckling"][i] /
                        (I_support_span * params["B Flexural Stess Buckling"][i]))

        # --- Factors of Safety ---
        FOS_c5.append(sigma1 / flange_stress)
        FOS_c6.append(sigma2 / tips_stress)
        FOS_c7.append(sigma3 / web_stress)
        FOS_c8.append(tau    / flexural_stress)

    return (min(params["strength_tension"] / tens,
        params["strength_compression"] / comp,
        params["strength_shear"] / shear,
        params["strength_glue"] / glue))




# helper for σ buckling formulas
def sigma_buckling(C, t, b, E, denom):
    return (C * math.pi**2 * E / denom) * (t / b)**2

# helper for τ buckling formula
def tau_buckling(t, h, a, E, denom):
    return (5 * math.pi**2 * E / denom) * ((t / h)**2 + (t / a)**2)


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

if beam_type == "nonuniform":
    params = uniform_params
    beam = build_beam(params)
    print("FoS =", analyze_uniform_fos(params, beam))
    #analyze_uniform_maxP(params, beam)

else:
    params = nonuniform_params
    optimize_split(params)
    beam = build_beam(params)
    analyze_nonuniform_maxP(params, beam)
