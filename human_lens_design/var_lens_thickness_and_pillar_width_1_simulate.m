clearvars;
close all;
clc;

addpath('./utils')

basefilename = 'sims_';
res_dir = './results/variable_thickness_and_pillar_widths/';
amp_comp = 0.27;
x_ext = 200e-3;

use_inverted_lens = false;
focal_length_mm = 80;

%% simulation without lens

use_lens = false;
use_delays = 1;
seed = 1;

doLensSimulation(basefilename, res_dir, seed, use_lens, [], [], [], use_delays, focal_length_mm, amp_comp, x_ext);

%% simulation with flat lens

use_lens = true;
use_delays = 1;
seed = 1;
lens_thickness_mm = 11;
pillar_width = 0;

doLensSimulation(basefilename, res_dir, seed, use_lens, use_inverted_lens, lens_thickness_mm, pillar_width, use_delays, focal_length_mm, amp_comp, x_ext);

%% do simulations with flat lens of varying thickness

use_lens = true;
use_delays = 1;

for pillar_width=1:2:9
    for lens_thickness_mm = 4:11 %in mm
        for seed=1:20
            doLensSimulation(basefilename, res_dir, seed, use_lens, use_inverted_lens, lens_thickness_mm, pillar_width, use_delays, focal_length_mm, amp_comp, x_ext);
        end
    end
end
