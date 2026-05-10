from modules.ml_model import get_recommendation

# Wool should be High impact → switch suggestion
print(get_recommendation("Wool", ["Bleach Wash", "Bio-Polishing"]))

# Cotton (Conv.) should be Medium impact → acceptable + process tweaks
print(get_recommendation("Cotton (Conv.)", ["Reactive Dyeing"]))

# Polyester should be Low impact → acceptable
print(get_recommendation("Polyester", ["Digital Printing"]))
