import pycba as cba
import numpy as np
import matplotlib.pyplot as plt


class BeamModel:
    def __init__(self, EI=100.):
        self.L = []  # span boundaries
        self.LM = [[0, 0, 0, 0, 0]]  # load matrix
        self.EI = EI
        self.R = [-1, -1]  # support reactions
        self.beam_analysis = None

    def add_support(self, distance, support_type):

        if support_type == "roller":
            self.L.append(distance)
            self.R.extend([-1, 0])
        elif support_type == "pin":
            self.L.append(distance)
            self.R.extend([-1, -1])
        else:
            raise ValueError("Support type must be 'roller' or 'pin'.")

    def identify_span(self, distance):
        if not self.L:
            raise ValueError("No spans defined.")

        if distance < self.L[0]:
            return 1

        for i in range(1, len(self.L)):
            if self.L[i - 1] <= distance < self.L[i]:
                return i + 1

        raise ValueError("Distance exceeds beam length.")

    def add_point_load(self, weight, distance):
        span = self.identify_span(distance)
        self.LM.append([span, 2, weight, distance, 0])

    def add_udl(self, distance, udl):
        if not self.beam_analysis:
            self.beam_analysis = cba.BeamAnalysis(self.L, self.EI, self.R, self.LM)

        span = self.identify_span(distance)
        self.beam_analysis.add_udl(i_span=span, w=udl)

    def analyze(self, n_points=10000):
        self.beam_analysis = cba.BeamAnalysis(self.L, self.EI, self.R, self.LM)
        self.beam_analysis.analyze(n_points)
        print("Reactions (N):", self.beam_analysis.beam_results.R)
        print("Max moment (Nm):", self.beam_analysis.beam_results.vRes[0].M.max())
        print("Max shear (N):", self.beam_analysis.beam_results.vRes[0].V.max())

    def display(self):
        if not self.beam_analysis:
            raise RuntimeError("Beam not analyzed yet.")
        self.beam_analysis.plot_results()
