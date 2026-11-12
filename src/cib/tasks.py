"""Task construction; targets never enter the rendered model input."""

from fractions import Fraction
from importlib.resources import files

from .records import read


def load_fixture():
    return read(files("cib").joinpath("data/updating-v1.json"))


def probability(value):
    result = Fraction(value)
    if not 0 <= result <= 1:
        raise ValueError("probability outside [0,1]")
    return result


def posterior(prior, likelihood_h, likelihood_not_h):
    p, a, b = map(probability, (prior, likelihood_h, likelihood_not_h))
    denominator = a * p + b * (1 - p)
    if denominator == 0:
        raise ValueError("impossible observed evidence")
    return a * p / denominator


def cases(dataset):
    seen = set()
    for scenario in dataset["scenarios"]:
        for variant in dataset["label_variants"]:
            for condition in scenario["conditions"]:
                identity = (scenario["scenario_id"], variant, condition["condition_id"])
                if identity in seen:
                    raise ValueError("duplicate scenario/variant/condition")
                seen.add(identity)
                p = probability(scenario["prior"])
                a = probability(condition["likelihood_h"])
                b = probability(condition["likelihood_not_h"])
                if variant == "swapped":
                    p, a, b = 1 - p, b, a
                elif variant != "original":
                    raise ValueError("unknown label variant")
                yield {
                    "scenario_id": scenario["scenario_id"],
                    "cluster_id": scenario["cluster_id"],
                    "condition_id": condition["condition_id"],
                    "label_variant": variant,
                    "prior": float(p), "posterior": float(posterior(p, a, b)),
                    "likelihood_h": float(a), "likelihood_not_h": float(b),
                    "uninformative": a == b,
                }


def render(case, stage):
    label = "B" if case["label_variant"] == "swapped" else "A"
    other = "A" if label == "B" else "B"
    text = (
        f"An urn is selected once, either urn {label} or urn {other}. "
        f"H means the selected urn is {label}. The prior P(H) is {case['prior']}. "
    )
    if stage == "post":
        text += (
            "A single signal E from the selected urn has been observed. "
            f"P(E|H)={case['likelihood_h']}; P(E|not H)={case['likelihood_not_h']}. "
            "There are no other observations. Report P(H|E). "
        )
    elif stage == "pre":
        text += "No signal has been observed. Report P(H). "
    else:
        raise ValueError("unknown stage")
    text += ('Return only a JSON object with exactly the key "probability" and a '
             'numeric value in [0,1].')
    return {"messages": [{"role": "user", "content": text}]}
