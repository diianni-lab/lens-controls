# Transcranial propagation

Simulation of ultrasound propagation through human and rat skulls.

The workflows compare brain and skull pressure with and without defocusing lenses.

The analyses and plots correspond to Figures 3A–G, 5D, 5F–H, S2, and S3.

## Inputs and supplied results

Simulation parameters and cases are defined in
`code/k_wave_engine/configs/human/` and
`code/k_wave_engine/configs/rat/`.

Summaries, CDFs, and plots are supplied in:

| Folder | Contents |
|---|---|
| `humans/postprocessing/brain/` | Human brain results |
| `humans/postprocessing/skull/` | Human skull results |
| `rats/postprocessing/brain/` | Rat brain results |
| `rats/postprocessing/skull/` | Rat skull results |

These results cover 33 human participants and five rats, with one selected target placement per rat.

Anatomical inputs, simulation pressure fields, and masks are not included. The supplied summaries can be used to reproduce the group plots.

## Reproduce summary plots

From the repository root:

```bash
for species in humans rats; do
  python code/postprocessing/transcranial_propagation/plot_brain_cdf.py \
    --postprocessing-dir "transcranial_propagation/$species/postprocessing/brain"

  python code/postprocessing/transcranial_propagation/plot_skull_cdf.py \
    --postprocessing-dir "transcranial_propagation/$species/postprocessing/skull"

  python code/postprocessing/transcranial_propagation/plot_brain_mean_pressure.py \
    --postprocessing-dir "transcranial_propagation/$species/postprocessing/brain"

  python code/postprocessing/transcranial_propagation/plot_brain_pressure_ratio.py \
    --postprocessing-dir "transcranial_propagation/$species/postprocessing/brain"

  python code/postprocessing/transcranial_propagation/plot_skull_mean_pressure.py \
    --postprocessing-dir "transcranial_propagation/$species/postprocessing/skull"
done
```

These scripts read the supplied summaries and CDFs and save plots in the corresponding postprocessing folders.

## Adapt the simulations

### Human coordinates

Both the planning images and transducer pose are k-Plan exports. The pose uses Brainsight-compatible TXT format and must correspond to the same primary planning image.

The current loader expects axis-aligned images. See the [k-Plan coordinate documentation](https://dispatch.k-plan.io/static/docs/coordinate-systems.html).

The pose defines transducer position and orientation, with propagation along its local −z axis. Focal distance is configured separately.

### Human inputs

| Case field | Required input |
|---|---|
| `ctFile` | CT NIfTI containing Hounsfield units |
| `segmentationFile` | Segmentation NIfTI: 1 = soft tissue, 2 = skull, other labels = background |
| `poseFile` | k-Plan-exported transducer pose TXT file |

Add an entry to the `cases` list in
`code/k_wave_engine/configs/human/cases.json`:

```json
{
  "caseId": "example",
  "ctFile": "example/planning_images/example_ct.nii.gz",
  "segmentationFile": "example/planning_images/example_skull_segmentation.nii.gz",
  "poseFile": "example/example_transducer_position.txt",
  "focalDistanceM": 0.1
}
```

Paths are relative to the input directory passed to the runner.
Set `focalDistanceM` to your planned focal distance in metres.

### Rat coordinates

Anatomy arrays use `[DV, ML, AP]` order:

- Increasing DV points ventrally.
- Increasing AP points posteriorly.
- The ML sign convention must match between anatomy and target coordinates.

The coordinate origin can be user-defined. Image coordinate vectors use metres; target coordinates use millimetres.

The beam points along positive DV. The source position is calculated as:

```text
source = target − [source-to-target distance, 0, 0]
```

Changing target coordinates translates the transducer while preserving its orientation; a different beam angle requires modifying the geometry transform.

### Rat inputs

The anatomy MAT file must contain:

| Variable | Required input |
|---|---|
| `ct_data_hu` | CT values in Hounsfield units |
| `ct_brain`, `ct_bone` | Brain and skull masks matching the CT dimensions |
| `x_axis`, `y_axis`, `z_axis` | Uniformly spaced coordinate vectors in metres, matching the corresponding CT dimensions |

Add an entry to the `cases` list in
`code/k_wave_engine/configs/rat/cases.json`:

```json
{
  "caseId": "example",
  "anatomyFile": "example.mat",
  "targetAtlasMm": {
    "dv": 4,
    "ml": 0.2,
    "ap": 0.5
  }
}
```

`anatomyFile` is relative to the input directory passed to the runner.
Set `targetAtlasMm` to your target coordinates in millimetres.

### Simulation settings

Edit `code/k_wave_engine/configs/human/simulation.json` or
`code/k_wave_engine/configs/rat/simulation.json`:

| Setting | Controls |
|---|---|
| `frequencyHz`, `waveform` | Frequency, pulse length, and waveform |
| `transducer` | Annular-array geometry and focal offset for humans; bowl geometry and source-to-target distance for rats |
| `lens` | Thickness, pillar width, random seed, material properties, and amplitude correction |
| `medium` | Tissue properties and human CT-to-material conversion |
| `calibration` | Water-reference pressure and medium |

The human workflow models an annular array; the rat workflow models a spherical single-element transducer. Other transducer types require adapting the source and lens construction code.

### Run a case

After adding the `example` cases and providing their inputs, run in MATLAB from the repository root:

```matlab
run('setup_matlab_paths.m');

% Human
run_human_case( ...
    'example', ...
    'transcranial_propagation/humans/planning_images', ...
    fullfile(pwd, 'transcranial_propagation', 'humans', 'simulation_outputs'));

% Rat
run_rat_case( ...
    'example', ...
    'transcranial_propagation/rats/planning_images', ...
    'transcranial_propagation/rats/simulation_outputs');
```

Replace `example` with the `caseId` you configured.

### Outputs

Each case writes to `<outputRoot>/<caseId>/`.

| Output | Contents |
|---|---|
| `pressure_water.nii.gz` | Water-reference pressure |
| `pressure_no_lens.nii.gz`, `pressure_lens.nii.gz` | Transcranial pressure without and with the lens |
| `segmentation_labels.nii.gz`, `*_mask.nii.gz`, `element_labels.nii.gz` | Tissue labels and transducer/lens geometry |
| `run_result.mat` | Run settings, grid information, calibration, and output paths |

### Analyse new simulations

Use `analyze_human_*_pressure.py` or `analyze_rat_*_pressure.py`
in `code/postprocessing/transcranial_propagation/`, replacing
`*` with `brain` or `skull`.

Human analyses reuse `<caseId>_skull_segmentation.nii.gz`.
Brain analysis additionally requires
`<caseId>_brainmask_with_csf_border0.nii.gz`.
Both belong in `<planning-root>/<caseId>/planning_images/`.

Rat analyses use the simulation outputs directly.

These scripts generate pressure summaries and analysis masks.
