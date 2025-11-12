from beam_functions import BeamModel

beam = BeamModel()
beam.add_support(3, "pin")
beam.add_support(5, "roller")
beam.add_support(10, "roller")

beam.add_support(11, "pin")

beam.add_support(12, "roller")


beam.add_point_load(20, 2)
beam.add_point_load(120, 10)

beam.analyze_train(100)
beam.display()