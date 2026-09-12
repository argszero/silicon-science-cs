"""Corpus v5 for issue #1: length-matched family, non-tell question, answer cue.

v2 exposed a BM25 confound: the gold line was the shortest of its template family
(it carried no status word), so BM25's length normalisation ranked gold first in
every cell for a reason unrelated to semantic robustness. v3 removes the confound by
construction: gold, status distractors and entity distractors are all produced from
ONE parameterised template with the same number of tokens, so every line in the
answer-bearing family has an identical token length.

Template: "Archive record {n}: the {s} vault code for the {e} sector {v} {code}."
  gold              : s = "current",  e = target entity, v = "is"
  status distractor : s = a status word, e = target entity, v = "was" or "is"
  entity distractor : s = "current",  e = other entity,  v = "is"

The question asks for the current code, so gold is the unique line with s=current and
e=target. Ground truth remains exact by construction.

Filler arms (pure length, no competition for the answer):
  neutral : out-of-domain records
  related : in-domain records about the SAME entity but a DIFFERENT field
"""
import random

ENTITIES = [
    "red", "blue", "green", "amber", "violet", "silver", "crimson", "teal",
    "indigo", "maroon", "navy", "olive", "plum", "rust", "sable", "topaz",
    "umber", "wheat", "zinc", "azure", "bronze", "coral", "denim", "ebony",
    "fawn", "gold", "hazel", "ivory", "jade", "khaki", "lilac", "mauve",
    "ochre", "pearl", "quartz", "rose", "sage", "taupe", "verdi", "onyx",
]

STATUS_WORDS = ["previous", "proposed", "retired", "backup", "draft", "historic"]

LINE_TEMPLATE = "Archive record {n}: the {s} vault code for the {e} sector {v} {code}."

NEUTRAL_FILLER = [
    "Shipping manifest {n} lists {k} crates bound for the {city} depot.",
    "Maintenance note {n} records {k} lamps replaced along the {city} road.",
    "Quarterly filing {n} settles {k} invoices raised by the {city} branch.",
    "Field survey {n} counted {k} nesting pairs near the {city} reservoir.",
    "Inventory sheet {n} stores {k} spare parts inside the {city} yard.",
    "Drainage report {n} measured {k} millimetres across the {city} district.",
]

RELATED_FIELDS = [("storage capacity", "units"), ("audit window", "days"),
                  ("inspection interval", "hours"), ("crate allowance", "crates"),
                  ("power draw", "kilowatts"), ("chiller setpoint", "degrees")]
RELATED_TEMPLATE = "Archive record {n}: the {field} for the {e} sector is {k} {unit}."

CITIES = ["Harrow", "Belmont", "Cairn", "Dunmore", "Elmsted", "Fairview", "Grafton",
          "Hollis", "Iverton", "Jarrow", "Kelby", "Larkspur", "Marlow", "Norwood"]


def code_for(i):
    return "{:04d}".format(1000 + (i * 7919) % 9000)


def make_instance(inst_id, n_chunks, interference, kind="status", filler="related",
                  gold_frac=0.5, seed=1234, entity=None):
    """Build one instance with a length-matched answer-bearing family.

    kind: "status" (distractors share entity+field, differ by status) or
          "entity" (distractors share field, differ by entity).
    filler: "neutral" or "related".
    """
    rng = random.Random(seed * 1000003 + inst_id)
    ent = entity if entity is not None else ENTITIES[inst_id % len(ENTITIES)]
    others = [e for e in ENTITIES if e != ent]
    rng.shuffle(others)
    gold_code = code_for(inst_id)
    q_text = ("Question: which vault code applies to the " + ent +
              " sector at present? Answer: the vault code is")
    retriever_query = "which vault code applies to the " + ent + " sector at present?"

    n_dist = int(round(n_chunks * interference))
    n_fill = max(1, n_chunks - n_dist - 1)
    lines = []
    for j in range(n_dist):
        c = code_for(inst_id + 137 * (j + 1))
        if kind == "status":
            sw = STATUS_WORDS[j % len(STATUS_WORDS)]
            verb = "was" if sw in ("previous", "retired", "historic") else "is"
            s_val, e_val = sw, ent
        else:
            s_val, e_val = "current", others[j % len(others)]
        lines.append({"kind": "distract", "sub": kind, "s": s_val, "e": e_val,
                      "text": LINE_TEMPLATE.format(n=inst_id + 2 + j, s=s_val, e=e_val,
                                                   v="is", code=c),
                      "entity": e_val, "code": c})
    for j in range(n_fill):
        if filler == "neutral":
            ft = NEUTRAL_FILLER[(inst_id + j) % len(NEUTRAL_FILLER)]
            txt = ft.format(n=1000 + inst_id * 97 + j, k=10 + (j * 37) % 900,
                            city=CITIES[(inst_id + j) % len(CITIES)])
        else:
            field, unit = RELATED_FIELDS[(inst_id + j) % len(RELATED_FIELDS)]
            txt = RELATED_TEMPLATE.format(n=1000 + inst_id * 97 + j, e=ent, field=field,
                                          k=10 + (j * 37) % 900, unit=unit)
        lines.append({"kind": "fill", "sub": filler, "text": txt})
    pos = int(round(gold_frac * len(lines)))
    pos = max(0, min(len(lines), pos))
    gold_text = LINE_TEMPLATE.format(n=inst_id + 1, s="current", e=ent, v="is", code=gold_code)
    lines.insert(pos, {"kind": "gold", "sub": "gold", "s": "current", "e": ent, "v": "is",
                       "text": gold_text, "entity": ent, "code": gold_code})
    for i, ln in enumerate(lines):
        ln["idx"] = i
    return {"inst_id": inst_id, "entity": ent, "gold_code": gold_code, "question": q_text,
            "retriever_query": retriever_query,
            "gold_text": gold_text, "gold_pos": pos, "n_chunks": len(lines),
            "n_distract": n_dist, "n_fill": n_fill, "interference": interference,
            "kind": kind, "filler": filler, "gold_frac": gold_frac, "seed": seed,
            "lines": lines}


def context_text(instance, chunk_indices):
    body = " ".join(instance["lines"][i]["text"] for i in chunk_indices)
    return body + " " + instance["question"]


def all_indices(instance):
    return [ln["idx"] for ln in instance["lines"]]


def oracle_indices(instance):
    return [instance["gold_pos"]]


def no_evidence_indices(instance):
    return [ln["idx"] for ln in instance["lines"] if ln["kind"] != "gold"]


def family_indices(instance):
    return [ln["idx"] for ln in instance["lines"] if ln["kind"] in ("gold", "distract")]


QUESTION_TELL_WORDS = ("current",)


def tell_audit(instance):
    """Check that no word unique to the gold line also appears in the question.

    A shared word would let a lexical retriever identify gold without any semantic
    discrimination, which invalidates the lexical arm of the comparison.
    """
    qt = set(w.lower().strip("?.,:") for w in instance.get("retriever_query", instance["question"]).split())
    gold_terms = set(w.lower().strip(".") for w in instance["gold_text"].split())
    others = set()
    for ln in instance["lines"]:
        if ln["kind"] != "gold":
            others |= set(w.lower().strip(".") for w in ln["text"].split())
    unique_gold = gold_terms - others
    shared = sorted(unique_gold & qt)
    return {"question_tokens": sorted(qt), "gold_unique_tokens": sorted(unique_gold),
            "shared_with_question": shared, "clean": len(shared) == 0}
