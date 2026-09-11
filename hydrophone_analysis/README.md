# Hydrophone analysis

Validation of human and rat defocusing lenses using hydrophone measurements.

The workflows compare measured and simulated pressure fields with and without lenses in the XZ and XY planes.

The analyses and plots correspond to Figures 2C and 5E.

## Inputs and supplied results

Hydrophone measurements and simulation inputs are supplied for the lens and no-lens conditions.

| Folder | Contents |
|---|---|
| `data/human/hydrophone/` | Hydrophone measurements |
| `data/human/simulation/` | Simulation results |
| `data/rat/hydrophone/` | Hydrophone measurements |
| `data/rat/simulation/` | Simulation results |
| `output/human/` | Human pressure-ratio summaries and plots |
| `output/rat/` | Rat pressure-ratio summaries and plots |

## Reproduce the results

From the repository root:

### Human

```bash
python code/postprocessing/hydrophone_analysis/analyze_human_pressure_ratios.py \
  --data-root hydrophone_analysis/data/human \
  --output-dir hydrophone_analysis/output/human

python code/postprocessing/hydrophone_analysis/plot_pressure_ratios.py \
  --dataset human \
  --data-root hydrophone_analysis/data/human \
  --output-dir hydrophone_analysis/output/human
```

### Rat

```bash
python code/postprocessing/hydrophone_analysis/analyze_rat_pressure_ratios.py \
  --data-root hydrophone_analysis/data/rat \
  --output-dir hydrophone_analysis/output/rat

python code/postprocessing/hydrophone_analysis/plot_pressure_ratios.py \
  --dataset rat \
  --data-root hydrophone_analysis/data/rat \
  --output-dir hydrophone_analysis/output/rat
```

These commands calculate pressure ratios using the no-lens −6-dB region and regenerate the plots.
