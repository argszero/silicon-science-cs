# Result table (generated from canonical_results.json)

Gold-answer mean log-probability in nats; retrieval is the dense retriever at $k=4$. Sampled exact intervals are Wilson 95% over 8 decodes (2 instances x 4 seeds).

| context (chunks) | interference | reading | retrieval k=4 | gap | greedy exact | sampled exact (Wilson 95%) |
|---|---|---|---|---|---|---|
| 64 | 0.00 | -0.180 | -0.146 | +0.033 | 2/2 | 1.000 [0.676, 1.000] |
| 64 | 0.15 | -0.304 | -0.378 | -0.074 | 2/2 | 0.500 [0.215, 0.785] |
| 64 | 0.30 | -0.354 | -1.351 | -0.997 | 1/2 | 0.375 [0.137, 0.694] |
| 64 | 0.45 | -0.465 | -1.340 | -0.874 | 1/2 | 0.250 [0.071, 0.591] |
| 64 | 0.60 | -0.792 | -2.016 | -1.223 | 0/2 | 0.125 [0.022, 0.471] |
| 64 | 0.80 | -0.759 | -2.016 | -1.256 | 0/2 | 0.125 [0.022, 0.471] |
| 128 | 0.00 | -0.228 | -0.154 | +0.074 | 2/2 | 1.000 [0.676, 1.000] |
| 128 | 0.15 | -0.653 | -1.351 | -0.698 | 1/2 | 0.125 [0.022, 0.471] |
| 128 | 0.30 | -0.676 | -2.016 | -1.340 | 1/2 | 0.000 [0.000, 0.324] |
| 128 | 0.45 | -0.662 | -2.016 | -1.354 | 1/2 | 0.000 [0.000, 0.324] |
| 128 | 0.60 | -0.999 | -2.029 | -1.030 | 0/2 | 0.000 [0.000, 0.324] |
| 128 | 0.80 | -0.893 | -2.008 | -1.115 | 0/2 | 0.000 [0.000, 0.324] |
| 256 | 0.00 | -0.206 | -0.127 | +0.079 | 2/2 | 1.000 [0.676, 1.000] |
| 256 | 0.15 | -0.551 | -2.016 | -1.465 | 2/2 | 0.375 [0.137, 0.694] |
| 256 | 0.30 | -0.687 | -2.029 | -1.341 | 1/2 | 0.125 [0.022, 0.471] |
| 256 | 0.45 | -0.683 | -1.973 | -1.291 | 1/2 | 0.000 [0.000, 0.324] |
| 256 | 0.60 | -1.101 | -1.856 | -0.755 | 0/2 | 0.000 [0.000, 0.324] |
| 256 | 0.80 | -1.043 | -1.877 | -0.834 | 0/2 | 0.000 [0.000, 0.324] |

## Summary statistics

- retrieval minus reading, by interference: 0.00: +0.062, 0.15: -0.745, 0.30: -1.226, 0.45: -1.173, 0.60: -1.003, 0.80: -1.069
- retrieval leads in 3 of 6 cells without distractors and in 2 of 30 cells with distractors
- length-only sweep (reading, I=0): L=128: -0.228, L=256: -0.206, L=64: -0.180
- distractor type at matched density: same-entity reading -1.101 against retrieval -1.856; different-entity reading -1.700 against retrieval -0.468
- evidence position (reading): 0.0: -0.400, 0.25: -1.054, 0.5: -1.101, 0.75: -0.610, 1.0: -0.207
- pooled gold recovery over the 30 distractor cells: dense 3/30 (k=1), 5/30 (k=4), 15/30 (k=8); BM25 0/30 (k=4)
