import random

_TRANSFORMS = [
    lambda name: name.upper().replace(" ", "").replace(",", "") + ".COM",
    lambda name: name.split()[0][:4].upper() + "*SUBSCRIPTION",
    lambda name: name.upper() + " INC",
    lambda name: name.split()[0].upper(),
]


def inject_noise(merchant_name: str, rng: random.Random | None = None) -> str:
    rng = rng or random
    transform = rng.choice(_TRANSFORMS)
    return transform(merchant_name)
