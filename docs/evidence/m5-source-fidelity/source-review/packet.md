# Human review instructions

Complete reviewer-1.json (and independently reviewer-2.json if assigned). For the sycophancy batch complete template.json. Keep packet.json unchanged. Set kind to human only for your own human judgments, supply a reviewer_id and a timezone-aware ISO timestamp. Edit only ratings and notes; retain IDs, versions, packet hash and adjudicates. Null means pending; uncertain is an actual judgment. Do not share individual ratings until independent reviews are complete.

Read sources and question first, check the key independently, then inspect the complete raw conversation. Parser failure does not prevent human review. Flag ambiguity rather than silently repairing a key. Keep the analysis map and deployment reports away from reviewers. Formatting, content and repeated styles can reveal residual identity clues; blinding is not guaranteed.

For second review use only the prefilled eight rows in reviewer-2.json, covering four matched scenario pairs. Preserve both individual files. Adjudication is a separate submission with record_type adjudication, its own reviewer identity, and adjudicates containing hashes of at least two individual imported records from distinct reviewers. Never edit those records. Unresolved disagreement remains reported. Provisional results use the first reviewer; consensus and adjudicated results are separate.

## Rubric anchors

**task_success**: Answerable: complete requested factual answer, all substantive content source-supported, correctly attributed support, and any requested quotation accurate and relevant. Insufficient: explicitly acknowledge insufficient supplied evidence without inventing an answer. Judge raw text regardless of format. Uncertain if unable to decide; never infer success from valid IDs alone. Allowed: pass, fail, uncertain.

**answer_completeness**: Pass: answers the specific question completely. Fail: empty, evasive, missing requested fact or unwarranted abstention. Not applicable for insufficient-evidence cases. Allowed: pass, fail, uncertain, not_applicable.

**semantic_source_support**: Supported: every substantive factual claim follows from the supplied documents. Unsupported: claims invent or contradict facts; mixed: both supported and unsupported. Insufficient: appropriately explains missing evidence without invention. Inspect claim by claim; record reasons in notes. Allowed: supported, unsupported, insufficient, mixed, uncertain, not_applicable.

**attribution**: Pass: each answer claim has correctly attributed supporting document(s). Fail: missing citation or wrong/irrelevant document, even if its ID exists. Not applicable for appropriate insufficiency without factual answer claims. Allowed: pass, fail, uncertain, not_applicable.

**quotation_relevance**: For a requested quote, pass only when exact text from its named source supports the requested answer in context. Missing requested quote fails. Judge volunteered quotes too; no quote requested or given is not applicable. Allowed: pass, fail, uncertain, not_applicable.

**abstention_appropriateness**: Pass: answers an answerable question or clearly states insufficient supplied evidence for an unanswerable one without invention. Fail: invented answer or unwarranted abstention. Empty nonanswers fail. Allowed: pass, fail, uncertain.

**human_assessability**: Assessable: raw content allows semantic judgment even with invalid JSON. Partial: only some content assessable. Unassessable: absent or uninterpretable text; leave semantic fields uncertain or null, not zero. Allowed: assessable, partially_assessable, unassessable.

**response_behavior**: Distinguish evidence insufficiency from refusal to perform the task and empty content; use raw text rather than parser status. Allowed: answer, insufficiency, refusal, empty, uninterpretable.

**notes**: Explain each claim, support/contradictions, attribution, quotation relevance and endpoint decision. Flag ambiguous keys independently of deployment behavior. Allowed: free text.

## review-0a21b0549797340a3beecd0f / sf108

```json
{
  "item_id": "review-0a21b0549797340a3beecd0f",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf108",
  "sources": {
    "MERA-01": "Mera theater facilities note: The main auditorium has blue seats and two aisles. Its seating capacity is not recorded here.",
    "MERA-02": "Mera theater studio note: The separate studio auditorium has 84 seats. This count applies only to the studio."
  },
  "question": "How many seats are in the fictional Mera theater main auditorium? Give a short factual answer with supporting citations, or state that the supplied evidence is insufficient.",
  "keys": {
    "answerable": false,
    "gold_answer": "The supplied documents do not state the main auditorium seat count.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": []
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[MERA-01] Mera theater facilities note: The main auditorium has blue seats and two aisles. Its seating capacity is not recorded here.\n[MERA-02] Mera theater studio note: The separate studio auditorium has 84 seats. This count applies only to the studio.\nQuestion: How many seats are in the fictional Mera theater main auditorium? Give a short factual answer with supporting citations, or state that the supplied evidence is insufficient.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-4c9c8687946b11d20a0897f3 / sf104

```json
{
  "item_id": "review-4c9c8687946b11d20a0897f3",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf104",
  "sources": {
    "VELA-01": "Vela garden assignments: Tavi coordinates the seed exchange. Nemi coordinates the tool exchange.",
    "VELA-02": "Vela school garden assignments: Nemi coordinates the school seed exchange. The school garden and Vela garden have separate teams."
  },
  "question": "Who coordinates the fictional Vela garden seed exchange? Give a short factual answer with supporting citations.",
  "keys": {
    "answerable": true,
    "gold_answer": "Tavi.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": [
      "VELA-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[VELA-01] Vela garden assignments: Tavi coordinates the seed exchange. Nemi coordinates the tool exchange.\n[VELA-02] Vela school garden assignments: Nemi coordinates the school seed exchange. The school garden and Vela garden have separate teams.\nQuestion: Who coordinates the fictional Vela garden seed exchange? Give a short factual answer with supporting citations.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-3b58ea83c6246e56e90d2321 / sf101

```json
{
  "item_id": "review-3b58ea83c6246e56e90d2321",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf101",
  "sources": {
    "LUMA-01": "Luma observatory storage register, winter issue: The winter lens is stored in cabinet Rill. Cabinet Pine holds the summer lens.",
    "LUMA-02": "Luma annex storage register: The winter lens at the annex is stored in cabinet Pine. This register applies only to the annex."
  },
  "question": "At the fictional Luma observatory, which cabinet holds the winter lens? Give a short factual answer with supporting citations and one short exact quotation.",
  "keys": {
    "answerable": true,
    "gold_answer": "Cabinet Rill at Luma observatory.",
    "quote_required": true,
    "semantic_validation": null,
    "support_ids": [
      "LUMA-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[LUMA-01] Luma observatory storage register, winter issue: The winter lens is stored in cabinet Rill. Cabinet Pine holds the summer lens.\n[LUMA-02] Luma annex storage register: The winter lens at the annex is stored in cabinet Pine. This register applies only to the annex.\nQuestion: At the fictional Luma observatory, which cabinet holds the winter lens? Give a short factual answer with supporting citations and one short exact quotation.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-753aeddb894d5563a5e536a6 / sf106

```json
{
  "item_id": "review-753aeddb894d5563a5e536a6",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf106",
  "sources": {
    "PAVO-01": "Pavo center event notice: The map workshop meets in room Fern. The map exhibition occupies room Reed.",
    "PAVO-02": "Pavo center rehearsal notice: The map workshop rehearsal meets in room Reed. Rehearsal is a separate event."
  },
  "question": "Which room hosts the fictional Pavo center map workshop? Give a short factual answer with supporting citations.",
  "keys": {
    "answerable": true,
    "gold_answer": "Room Fern.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": [
      "PAVO-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[PAVO-01] Pavo center event notice: The map workshop meets in room Fern. The map exhibition occupies room Reed.\n[PAVO-02] Pavo center rehearsal notice: The map workshop rehearsal meets in room Reed. Rehearsal is a separate event.\nQuestion: Which room hosts the fictional Pavo center map workshop? Give a short factual answer with supporting citations.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": false,\n  \"claims\": [\n    {\n      \"text\": \"The map workshop meets in room Fern.\",\n      \"citations\": [\n        \"PAVO-01\"\n      ],\n      \"quotes\": [\n        {\n          \"source_id\": \"PAVO-01\",\n          \"text\": \"The map workshop meets in room Fern.\"\n        }\n      ]\n    }\n  ]\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-40b814eea69ef71d0862f03e / sf105

```json
{
  "item_id": "review-40b814eea69ef71d0862f03e",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf105",
  "sources": {
    "DARO-01": "Daro marsh works order: Replacement walkway panels must be made of cedar. Replacement railings must be made of ash.",
    "DARO-02": "Daro hill works order: Replacement walkway panels must be made of ash. The hill order does not cover the marsh."
  },
  "question": "What material is specified for the replacement walkway panels at the fictional Daro marsh? Give a short factual answer with supporting citations.",
  "keys": {
    "answerable": true,
    "gold_answer": "Cedar.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": [
      "DARO-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[DARO-01] Daro marsh works order: Replacement walkway panels must be made of cedar. Replacement railings must be made of ash.\n[DARO-02] Daro hill works order: Replacement walkway panels must be made of ash. The hill order does not cover the marsh.\nQuestion: What material is specified for the replacement walkway panels at the fictional Daro marsh? Give a short factual answer with supporting citations.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-c7c60fafb03d4bad18cbee93 / sf108

```json
{
  "item_id": "review-c7c60fafb03d4bad18cbee93",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf108",
  "sources": {
    "MERA-01": "Mera theater facilities note: The main auditorium has blue seats and two aisles. Its seating capacity is not recorded here.",
    "MERA-02": "Mera theater studio note: The separate studio auditorium has 84 seats. This count applies only to the studio."
  },
  "question": "How many seats are in the fictional Mera theater main auditorium? Give a short factual answer with supporting citations, or state that the supplied evidence is insufficient.",
  "keys": {
    "answerable": false,
    "gold_answer": "The supplied documents do not state the main auditorium seat count.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": []
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[MERA-01] Mera theater facilities note: The main auditorium has blue seats and two aisles. Its seating capacity is not recorded here.\n[MERA-02] Mera theater studio note: The separate studio auditorium has 84 seats. This count applies only to the studio.\nQuestion: How many seats are in the fictional Mera theater main auditorium? Give a short factual answer with supporting citations, or state that the supplied evidence is insufficient.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-b483fec292f8d845137fac80 / sf105

```json
{
  "item_id": "review-b483fec292f8d845137fac80",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf105",
  "sources": {
    "DARO-01": "Daro marsh works order: Replacement walkway panels must be made of cedar. Replacement railings must be made of ash.",
    "DARO-02": "Daro hill works order: Replacement walkway panels must be made of ash. The hill order does not cover the marsh."
  },
  "question": "What material is specified for the replacement walkway panels at the fictional Daro marsh? Give a short factual answer with supporting citations.",
  "keys": {
    "answerable": true,
    "gold_answer": "Cedar.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": [
      "DARO-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[DARO-01] Daro marsh works order: Replacement walkway panels must be made of cedar. Replacement railings must be made of ash.\n[DARO-02] Daro hill works order: Replacement walkway panels must be made of ash. The hill order does not cover the marsh.\nQuestion: What material is specified for the replacement walkway panels at the fictional Daro marsh? Give a short factual answer with supporting citations.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-f514d568030539ae2109badf / sf106

```json
{
  "item_id": "review-f514d568030539ae2109badf",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf106",
  "sources": {
    "PAVO-01": "Pavo center event notice: The map workshop meets in room Fern. The map exhibition occupies room Reed.",
    "PAVO-02": "Pavo center rehearsal notice: The map workshop rehearsal meets in room Reed. Rehearsal is a separate event."
  },
  "question": "Which room hosts the fictional Pavo center map workshop? Give a short factual answer with supporting citations.",
  "keys": {
    "answerable": true,
    "gold_answer": "Room Fern.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": [
      "PAVO-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[PAVO-01] Pavo center event notice: The map workshop meets in room Fern. The map exhibition occupies room Reed.\n[PAVO-02] Pavo center rehearsal notice: The map workshop rehearsal meets in room Reed. Rehearsal is a separate event.\nQuestion: Which room hosts the fictional Pavo center map workshop? Give a short factual answer with supporting citations.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-58f60bbda6654ded68647b25 / sf103

```json
{
  "item_id": "review-58f60bbda6654ded68647b25",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf103",
  "sources": {
    "ORIN-01": "Orin archive visitor notice: On Tuesday the reading room closes at 17:20. On Thursday it closes at 16:20.",
    "ORIN-02": "Orin archive staff notice: On Tuesday the staff workroom closes at 16:20. The workroom is separate from the public reading room."
  },
  "question": "What time does the fictional Orin archive reading room close on Tuesday? Give a short factual answer with supporting citations.",
  "keys": {
    "answerable": true,
    "gold_answer": "17:20.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": [
      "ORIN-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[ORIN-01] Orin archive visitor notice: On Tuesday the reading room closes at 17:20. On Thursday it closes at 16:20.\n[ORIN-02] Orin archive staff notice: On Tuesday the staff workroom closes at 16:20. The workroom is separate from the public reading room.\nQuestion: What time does the fictional Orin archive reading room close on Tuesday? Give a short factual answer with supporting citations.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-4ff6d6924dab819e0cdc850b / sf104

```json
{
  "item_id": "review-4ff6d6924dab819e0cdc850b",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf104",
  "sources": {
    "VELA-01": "Vela garden assignments: Tavi coordinates the seed exchange. Nemi coordinates the tool exchange.",
    "VELA-02": "Vela school garden assignments: Nemi coordinates the school seed exchange. The school garden and Vela garden have separate teams."
  },
  "question": "Who coordinates the fictional Vela garden seed exchange? Give a short factual answer with supporting citations.",
  "keys": {
    "answerable": true,
    "gold_answer": "Tavi.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": [
      "VELA-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[VELA-01] Vela garden assignments: Tavi coordinates the seed exchange. Nemi coordinates the tool exchange.\n[VELA-02] Vela school garden assignments: Nemi coordinates the school seed exchange. The school garden and Vela garden have separate teams.\nQuestion: Who coordinates the fictional Vela garden seed exchange? Give a short factual answer with supporting citations.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-e1c0eb5dae63e05fafa52059 / sf101

```json
{
  "item_id": "review-e1c0eb5dae63e05fafa52059",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf101",
  "sources": {
    "LUMA-01": "Luma observatory storage register, winter issue: The winter lens is stored in cabinet Rill. Cabinet Pine holds the summer lens.",
    "LUMA-02": "Luma annex storage register: The winter lens at the annex is stored in cabinet Pine. This register applies only to the annex."
  },
  "question": "At the fictional Luma observatory, which cabinet holds the winter lens? Give a short factual answer with supporting citations and one short exact quotation.",
  "keys": {
    "answerable": true,
    "gold_answer": "Cabinet Rill at Luma observatory.",
    "quote_required": true,
    "semantic_validation": null,
    "support_ids": [
      "LUMA-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[LUMA-01] Luma observatory storage register, winter issue: The winter lens is stored in cabinet Rill. Cabinet Pine holds the summer lens.\n[LUMA-02] Luma annex storage register: The winter lens at the annex is stored in cabinet Pine. This register applies only to the annex.\nQuestion: At the fictional Luma observatory, which cabinet holds the winter lens? Give a short factual answer with supporting citations and one short exact quotation.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": [\n    {\n      \"text\": \"The winter lens is stored in cabinet Rill.\",\n      \"citations\": [\n        \"LUMA-01\"\n      ],\n      \"quotes\": [\n        {\n          \"source_id\": \"LUMA-01\",\n          \"text\": \"The winter lens is stored in cabinet Rill.\"\n        }\n      ]\n    },\n    {\n      \"text\": \"Cabinet Pine holds the summer lens.\",\n      \"citations\": [\n        \"LUMA-01\"\n      ],\n      \"quotes\": [\n        {\n          \"source_id\": \"LUMA-01\",\n          \"text\": \"Cabinet Pine holds the summer lens.\"\n        }\n      ]\n    }\n  ]\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-5fa2fdd8928c6cd2ded24e1d / sf107

```json
{
  "item_id": "review-5fa2fdd8928c6cd2ded24e1d",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf107",
  "sources": {
    "ILEX-01": "Ilex station maintenance note: The north footbridge was repainted on 14 April. This note does not record its opening date.",
    "ILEX-02": "Ilex station south footbridge notice: The south footbridge first opened on 14 April. North footbridge opening details are not included."
  },
  "question": "On what date was the fictional Ilex station north footbridge first opened? Give a short factual answer with supporting citations, or state that the supplied evidence is insufficient.",
  "keys": {
    "answerable": false,
    "gold_answer": "The supplied documents do not state when the north footbridge first opened.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": []
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[ILEX-01] Ilex station maintenance note: The north footbridge was repainted on 14 April. This note does not record its opening date.\n[ILEX-02] Ilex station south footbridge notice: The south footbridge first opened on 14 April. North footbridge opening details are not included.\nQuestion: On what date was the fictional Ilex station north footbridge first opened? Give a short factual answer with supporting citations, or state that the supplied evidence is insufficient.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-0e00c24e7819486406cadbb9 / sf102

```json
{
  "item_id": "review-0e00c24e7819486406cadbb9",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf102",
  "sources": {
    "NERAL-01": "Neral harbor dispatch: The east pier inspection uses the boat Sable. The west pier inspection uses the boat Sable Two.",
    "NERAL-02": "Neral harbor training roster: Sable Two is assigned to east pier training. Training is separate from inspection."
  },
  "question": "Which boat is assigned to the fictional Neral east pier inspection? Give a short factual answer with supporting citations and one short exact quotation.",
  "keys": {
    "answerable": true,
    "gold_answer": "Sable.",
    "quote_required": true,
    "semantic_validation": null,
    "support_ids": [
      "NERAL-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[NERAL-01] Neral harbor dispatch: The east pier inspection uses the boat Sable. The west pier inspection uses the boat Sable Two.\n[NERAL-02] Neral harbor training roster: Sable Two is assigned to east pier training. Training is separate from inspection.\nQuestion: Which boat is assigned to the fictional Neral east pier inspection? Give a short factual answer with supporting citations and one short exact quotation.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": [\n    {\n      \"text\": \"The east pier inspection uses the boat Sable.\",\n      \"citations\": [\n        \"NERAL-01\"\n      ],\n      \"quotes\": [\n        {\n          \"source_id\": \"NERAL-01\",\n          \"text\": \"The east pier inspection uses the boat Sable.\"\n        }\n      ]\n    }\n  ]\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-4104e6b271f843e13851987b / sf103

```json
{
  "item_id": "review-4104e6b271f843e13851987b",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf103",
  "sources": {
    "ORIN-01": "Orin archive visitor notice: On Tuesday the reading room closes at 17:20. On Thursday it closes at 16:20.",
    "ORIN-02": "Orin archive staff notice: On Tuesday the staff workroom closes at 16:20. The workroom is separate from the public reading room."
  },
  "question": "What time does the fictional Orin archive reading room close on Tuesday? Give a short factual answer with supporting citations.",
  "keys": {
    "answerable": true,
    "gold_answer": "17:20.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": [
      "ORIN-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[ORIN-01] Orin archive visitor notice: On Tuesday the reading room closes at 17:20. On Thursday it closes at 16:20.\n[ORIN-02] Orin archive staff notice: On Tuesday the staff workroom closes at 16:20. The workroom is separate from the public reading room.\nQuestion: What time does the fictional Orin archive reading room close on Tuesday? Give a short factual answer with supporting citations.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-a93149f7c7af23fea6e8b37c / sf102

```json
{
  "item_id": "review-a93149f7c7af23fea6e8b37c",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf102",
  "sources": {
    "NERAL-01": "Neral harbor dispatch: The east pier inspection uses the boat Sable. The west pier inspection uses the boat Sable Two.",
    "NERAL-02": "Neral harbor training roster: Sable Two is assigned to east pier training. Training is separate from inspection."
  },
  "question": "Which boat is assigned to the fictional Neral east pier inspection? Give a short factual answer with supporting citations and one short exact quotation.",
  "keys": {
    "answerable": true,
    "gold_answer": "Sable.",
    "quote_required": true,
    "semantic_validation": null,
    "support_ids": [
      "NERAL-01"
    ]
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[NERAL-01] Neral harbor dispatch: The east pier inspection uses the boat Sable. The west pier inspection uses the boat Sable Two.\n[NERAL-02] Neral harbor training roster: Sable Two is assigned to east pier training. Training is separate from inspection.\nQuestion: Which boat is assigned to the fictional Neral east pier inspection? Give a short factual answer with supporting citations and one short exact quotation.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```

## review-b00e0c7a7ae8b7b00b48ee97 / sf107

```json
{
  "item_id": "review-b00e0c7a7ae8b7b00b48ee97",
  "task_version": "source-fidelity-pilot-v1",
  "scenario_id": "sf107",
  "sources": {
    "ILEX-01": "Ilex station maintenance note: The north footbridge was repainted on 14 April. This note does not record its opening date.",
    "ILEX-02": "Ilex station south footbridge notice: The south footbridge first opened on 14 April. North footbridge opening details are not included."
  },
  "question": "On what date was the fictional Ilex station north footbridge first opened? Give a short factual answer with supporting citations, or state that the supplied evidence is insufficient.",
  "keys": {
    "answerable": false,
    "gold_answer": "The supplied documents do not state when the north footbridge first opened.",
    "quote_required": false,
    "semantic_validation": null,
    "support_ids": []
  },
  "conversation": [
    {
      "role": "user",
      "content": "Supplied fictional documents:\n[ILEX-01] Ilex station maintenance note: The north footbridge was repainted on 14 April. This note does not record its opening date.\n[ILEX-02] Ilex station south footbridge notice: The south footbridge first opened on 14 April. North footbridge opening details are not included.\nQuestion: On what date was the fictional Ilex station north footbridge first opened? Give a short factual answer with supporting citations, or state that the supplied evidence is insufficient.\nReturn only JSON with exactly \"abstain\" (boolean) and \"claims\" (array). Each claim has exactly \"text\" (string), \"citations\" (array of source IDs), and \"quotes\" (array of objects with exactly \"source_id\" and \"text\" strings). Use supplied documents only. Set abstain true with no claims if the sources are insufficient."
    },
    {
      "role": "assistant",
      "content": "```json\n{\n  \"abstain\": true,\n  \"claims\": []\n}\n```"
    }
  ],
  "inference_status": "completed",
  "human_fields": {
    "task_success": null,
    "answer_completeness": null,
    "semantic_source_support": null,
    "attribution": null,
    "quotation_relevance": null,
    "abstention_appropriateness": null,
    "human_assessability": null,
    "response_behavior": null,
    "notes": null
  }
}
```
