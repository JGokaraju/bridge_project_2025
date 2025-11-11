from beam_functions import BeamModel

beam = BeamModel()
beam.add_support(3, "pin")
beam.add_support(5, "roller")
beam.analyze_train(100)
beam.display()