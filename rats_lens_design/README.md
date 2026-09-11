# Rat lens design

Design and evaluation of defocusing lenses for the 1.5-MHz transducer used in rats.

The workflow optimizes pillar width and maximum lens height, with flat lenses as a comparison.

The analyses and plots correspond to Figures 5A–B and S1C–D.

## Inputs and supplied results

Lens, transducer, and sweep parameters are defined in
`code/k_wave_engine/configs/rat/lens_sweep/`.

Summaries, calibration tables, and plots are supplied in:

| Folder | Contents |
|---|---|
| `pressure_ratios/` | −6-dB and −12-dB pressure-ratio summaries and analysis settings |
| `simulation_outputs/calibration/` | Lens thickness and source-amplitude calibration tables |
| `pressure_ratios_plots/` | Lens optimization plots |

Full simulation pressure fields and masks are not included and must be regenerated using the simulation workflow below.

## Reproduce summary plots

```matlab
run('setup_matlab_paths.m');
cd('rats_lens_design');

% Pillar-width comparison
plot_lens_sweep_ratios_by_pillar_width( ...
    'pressure_ratios', 'pressure_ratios_plots');

% Lens-height and flat-lens comparison
plot_lens_sweep_ratios_by_height( ...
    'pressure_ratios', 'pressure_ratios_plots');
```

These functions read the supplied −6-dB and −12-dB summaries and save plots in `pressure_ratios_plots/`.

## Regenerate simulations

Run in `rats_lens_design/`:

```matlab
run_rat_lens_sweep('simulation_outputs');
```

The runner generates the no-lens reference and calculates the equivalent flat-lens thicknesses and source-amplitude corrections automatically.

| Workflow | Parameters |
|---|---|
| Flat lenses | Equivalent thicknesses calculated from the pillared-lens designs |
| Pillared lenses | Widths 0.25, 0.5, 1, 1.5, 2, 2.5, 3 mm; maximum heights 0.5–4 mm in 0.5-mm steps; 20 random layouts per configuration |

Simulation pressure fields, masks, and calibration tables are saved in `simulation_outputs/`.

## Calculate pressure ratios

After the full simulation sweep, run from the repository root:

```bash
python code/postprocessing/rats_lens_design/analyze_lens_sweep_pressure_ratios.py \
  --simulation-root rats_lens_design/simulation_outputs \
  --output-dir rats_lens_design/pressure_ratios
```

This calculates both −6-dB and −12-dB pressure ratios and replaces the summaries in `pressure_ratios/`.
