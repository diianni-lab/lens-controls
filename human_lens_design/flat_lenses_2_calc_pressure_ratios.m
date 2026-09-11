clearvars;
close all;
clc;

addpath('./utils')

mat_dir = './results/flat_lens_3mm_dist';

% Initialize an empty struct array to store all results
results = struct('thickness', {}, 'pillar_width', {}, 'seed', {}, 'pressure_ratio', {});
counter = 1;

focal_length_mm = 80;

db_drop = 6;
lin_drop = 10^(-db_drop/20);

res_dir = ['./results/flat_lens_3mm_dist/press_ratio_' num2str(db_drop) 'dB'];
if ~isdir(res_dir); mkdir(res_dir); end

%% no lens - calculate isosurface and volume

mat_file = 'sims_no_lens_focus_80_seed_1.mat';

load([mat_dir '/' mat_file]);

% calculate isosurface
p_min_min = min(p_min_all(:));
p_min_all = p_min_all/p_min_min;    % scale to peak 1

[X, Y, Z] = meshgrid(kgrid.x_vec, kgrid.y_vec, kgrid.z_vec);
X = pagetranspose(X);
Y = pagetranspose(Y);
Z = pagetranspose(Z);

isosurf = isosurface(X, Y, Z, p_min_all, lin_drop);

% plot isosurface. Note that x and y are inverted in the plot
isosurf_pl = patch(isosurf,'FaceColor','blue','EdgeColor','blue');
axis image
xlim([kgrid.x_vec(1) kgrid.x_vec(end)])
ylim([kgrid.y_vec(1) kgrid.y_vec(end)])
zlim([kgrid.z_vec(1) kgrid.z_vec(end)])

% Create an alphaShape object
shp = alphaShape(isosurf.vertices,0.1);

% Test which points are inside the alpha shape
points = [X(:), Y(:), Z(:)];
in_volume = inShape(shp, points);
in_volume = reshape(in_volume, size(p_min_all));

fh = figure; 
imagesc(squeeze(in_volume(:,:,round(size(p_min_all,3)/2))));
axis image;

saveas(fh,[res_dir '/segmented_surface.fig']);
saveas(fh,[res_dir '/segmented_surface.png']);

% plot pressure beam
plane_z = 0;
[~,plane_z_idx] = min(abs(kgrid.z_vec-plane_z));

press_beam_plot_xy = squeeze(p_min_all(:,:,plane_z_idx))*(-p_min_min);

fh = figure;
colormap(slanCM('Blues'));
imagesc(kgrid.y_vec*1e3,kgrid.x_vec*1e3,press_beam_plot_xy/1e6);
hold on
contour(kgrid.y_vec*1e3,kgrid.x_vec*1e3,press_beam_plot_xy/1e6,[lin_drop,lin_drop]*(-p_min_min/1e6),'k-','LineWidth',1.5);
axis image;
cbar = colorbar;
xlabel('y (mm)');
ylabel('x (mm)');
ylabel(cbar,'pressure (MPa)');
title('Pressure Field')

saveas(fh,[res_dir '/beam_plot_contour.fig']);
saveas(fh,[res_dir '/beam_plot_contour.png']);
saveas(fh,[res_dir '/beam_plot_contour.svg']);

%% lens position - exclude region between transducer and medium side of lens

lens_x_pos_kgrid = kgrid.x_vec(1)+5e-3+3e-3+11e-3;
invalid_x_idx = find(kgrid.x_vec<=lens_x_pos_kgrid);

%% no lens - calc pressure ratio

mat_file = 'sims_no_lens_focus_80_seed_1.mat';
load([mat_dir '/' mat_file]);

% exclude region between transducer and medium side of lens
p_min_all(invalid_x_idx,:,:) = NaN;

[avg_p_in,avg_p_out,p_ratio] = computePressureRatio(p_min_all, in_volume);

results_nolens.avg_p_in = avg_p_in;
results_nolens.avg_p_out = avg_p_out;
results_nolens.pressure_ratio = p_ratio;

%% variable thickness and pillar width

pillar_width = 0;
seed = 1;

for lens_thickness_mm = 1:11 %in mm
    mat_file = ['sims_' num2str(lens_thickness_mm) 'mm_lens_pillar_width_' num2str(pillar_width) '_focus_' num2str(focal_length_mm) '_seed_' num2str(seed) '.mat'];

    load([mat_dir '/' mat_file]);

    % exclude region between transducer and medium side of lens
    p_min_all(invalid_x_idx,:,:) = NaN;

    [avg_p_in,avg_p_out,p_ratio] = computePressureRatio(p_min_all, in_volume);

    % Store all parameters and result in struct
    results(counter).thickness = lens_thickness_mm;
    results(counter).pillar_width = pillar_width;
    results(counter).seed = seed;
    results(counter).avg_p_in = avg_p_in;
    results(counter).avg_p_out = avg_p_out;
    results(counter).pressure_ratio = p_ratio;
    
    counter = counter + 1;

end

%% save ratios

save([res_dir '/pressure_ratios.mat'], 'results','results_nolens','db_drop');
