from beam_functions import BeamModel

beam = BeamModel()
beam.add_support(3, "pin")
beam.add_support(5, "roller")
beam.add_point_load(20, 2)
beam.analyze()
beam.display()