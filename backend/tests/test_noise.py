import random

from app.services.noise import inject_noise


def test_inject_noise_is_deterministic_with_seeded_rng():
    rng = random.Random(42)
    result = inject_noise("Netflix Inc", rng=rng)
    assert result != "Netflix Inc"
    assert isinstance(result, str) and len(result) > 0


def test_inject_noise_covers_all_transforms():
    rng = random.Random(0)
    outputs = {inject_noise("Netflix Inc", rng=rng) for _ in range(50)}
    assert len(outputs) > 1
