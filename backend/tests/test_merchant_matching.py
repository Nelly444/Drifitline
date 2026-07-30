from app.services.merchant_matching import normalize_merchants


def test_groups_known_messy_netflix_variants():
    raw_names = ["NETFLIX INC", "NETF*SUBSCRIPTION", "NETFLIX INC"]
    mapping = normalize_merchants(raw_names)

    canonical = mapping["NETFLIX INC"]
    assert mapping["NETF*SUBSCRIPTION"] == canonical
    assert len({mapping[n] for n in raw_names}) == 1


def test_does_not_merge_unrelated_merchants():
    raw_names = ["AMAZON INC", "MCDONALD'S INC", "WALMART INC"]
    mapping = normalize_merchants(raw_names)

    assert len({mapping[n] for n in raw_names}) == 3


def test_canonical_name_is_most_frequent_variant():
    raw_names = ["AMAZON.COM", "AMAZON.COM", "AMAZON INC", "AMAZ*SUBSCRIPTION"]
    mapping = normalize_merchants(raw_names)

    assert mapping["AMAZON.COM"] == "AMAZON.COM"
    assert mapping["AMAZON INC"] == "AMAZON.COM"
    assert mapping["AMAZ*SUBSCRIPTION"] == "AMAZON.COM"
