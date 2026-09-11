# Questionnaire analysis

Analysis of auditory and somatosensory reports from active stimulation (without lens) and control stimulation (with lens).

The scripts generate the analyses and plots used in Figure 4, including subject-level reports, sensory category prevalence, the proportion reporting any sensation, and reports per subject.

## Inputs and supplied results

Input: `data/questionnaire_responses.csv`.

The dataset contains 29 participants. The scripts select 22 participants (11 per condition) using the participant ID range 21–44 and the `NoLens` and `Lens` condition labels.

The following outputs are supplied in `results/`:

| Output name | Figure panel |
|---|---|
| `subject_cluster_reports` | 4A |
| `cluster_prevalence` | 4B |
| `any_sensation` | 4C |
| `reports_per_subject` | 4D |

## Reproduce the results

```bash
cd questionnaires_analysis

python scripts/subject_cluster_reports.py \
  --data-path data/questionnaire_responses.csv --output-dir reproduced_results

python scripts/cluster_prevalence.py \
  --data-path data/questionnaire_responses.csv --output-dir reproduced_results

python scripts/any_sensation.py \
  --data-path data/questionnaire_responses.csv --output-dir reproduced_results

python scripts/reports_per_subject.py \
  --data-path data/questionnaire_responses.csv --output-dir reproduced_results
```

Outputs are written to `reproduced_results/`.
