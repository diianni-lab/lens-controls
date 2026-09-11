clearvars;
close all;
clc;

addpath('./utils')

basefilename = 'sims_';
res_dir = './results/variable_focus_9mm_lens_pillar_width_7/';
amp_comp = 0.27;
x_ext = 250e-3;

use_inverted_lens = false;
lens_thickness_mm = 9;
pillar_width = 7;

for focal_length_mm = 50:20:150

    % simulation without lens
    
    use_lens = false;
    use_delays = 1;
    seed = 1;

    doLensSimulation(basefilename, res_dir, seed, use_lens, [], [], [], use_delays, focal_length_mm, amp_comp, x_ext);
    
    % simulations with selected lens geometry
    
    use_lens = true;
    use_delays = 1;

    for seed = 1:20
        doLensSimulation(basefilename, res_dir, seed, use_lens, use_inverted_lens, lens_thickness_mm, pillar_width, use_delays, focal_length_mm, amp_comp, x_ext);
    end

end
