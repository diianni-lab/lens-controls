
clearvars;
close all;
clc;

res_dir = './results/flat_lens_3mm_dist/press_ratio_6dB';

load([res_dir '/pressure_ratios.mat']);

% Get unique values of thickness
thicknesses = unique([results.thickness]);
thicknesses = thicknesses(4:end);

pillar_width = 0;

% flat lens
for k = 1:length(thicknesses)
   flat_lens_pressure_ratio(k) = results(k).pressure_ratio;
end

%% look at all thicknesses with pillar width 5 mm

lenses_dir = './results/variable_thickness_and_pillar_widths/press_ratio_6dB';

load([lenses_dir '/pressure_ratios.mat']);

% Get unique values of thickness and pillar width
thicknesses = unique([results.thickness]);
pillar_width = 5;

% Initialize arrays to store means and standard deviations
means_5mm = zeros(length(thicknesses), length(pillar_width));
stds_5mm = zeros(length(thicknesses), length(pillar_width));

% Calculate means and standard deviations for each combination
for k = 1:length(thicknesses)
    % Find all pressure ratios for this combination
    idx = [results.thickness] == thicknesses(k) & ...
          [results.pillar_width] == pillar_width;
    ratios = [results(idx).pressure_ratio];
    
    means_5mm(k) = mean(ratios);
    stds_5mm(k) = std(ratios);
end

%% look at all thicknesses with pillar width 7 mm

% Get unique values of thickness and pillar width
thicknesses = unique([results.thickness]);
pillar_width = 7;

% Initialize arrays to store means and standard deviations
means_7mm = zeros(length(thicknesses), length(pillar_width));
stds_7mm = zeros(length(thicknesses), length(pillar_width));

% Calculate means and standard deviations for each combination
for k = 1:length(thicknesses)
    % Find all pressure ratios for this combination
    idx = [results.thickness] == thicknesses(k) & ...
          [results.pillar_width] == pillar_width;
    ratios = [results(idx).pressure_ratio];
    
    means_7mm(k) = mean(ratios);
    stds_7mm(k) = std(ratios);
end

%% look at all thicknesses with pillar width 9 mm

% Get unique values of thickness and pillar width
thicknesses = unique([results.thickness]);
pillar_width = 9;

% Initialize arrays to store means and standard deviations
means_9mm = zeros(length(thicknesses), length(pillar_width));
stds_9mm = zeros(length(thicknesses), length(pillar_width));

% Calculate means and standard deviations for each combination
for k = 1:length(thicknesses)
    % Find all pressure ratios for this combination
    idx = [results.thickness] == thicknesses(k) & ...
          [results.pillar_width] == pillar_width;
    ratios = [results(idx).pressure_ratio];
    
    means_9mm(k) = mean(ratios);
    stds_9mm(k) = std(ratios);
end


%% plot
% Create the plot
fh = figure(1);
hold on

plot(linspace(thicknesses(1),thicknesses(end),100),ones(1,100)*results_nolens.pressure_ratio,'k--',...
    'LineWidth',1.5,...
    'DisplayName', 'No lens');

plot(thicknesses,flat_lens_pressure_ratio, 'b', ...
    'LineWidth',1.5,...
    'DisplayName', 'Flat lens');

colors = slanCM('prism2',8);


errorbar(thicknesses, means_5mm, stds_5mm, '-o', ...
        'Color', colors(1,:), ...
        'LineWidth', 1.5, ...
        'MarkerSize', 8, ...
        'MarkerFaceColor', colors(1,:), ...
        'DisplayName', '5-mm pillars');

errorbar(thicknesses, means_7mm, stds_7mm, '-o', ...
        'Color', colors(2,:), ...
        'LineWidth', 1.5, ...
        'MarkerSize', 8, ...
        'MarkerFaceColor', colors(2,:), ...
        'DisplayName', '7-mm pillars');

errorbar(thicknesses, means_9mm, stds_9mm, '-o', ...
        'Color', colors(3,:), ...
        'LineWidth', 1.5, ...
        'MarkerSize', 8, ...
        'MarkerFaceColor', colors(3,:), ...
        'DisplayName', '9-mm pillars');

% Customize the plot
xlabel('Thickness (mm)', 'FontSize', 12)
ylabel('Pressure Ratio', 'FontSize', 12)
title(['Pressure ratio at ' num2str(-db_drop) ' dB'], 'FontSize', 14)
% grid on
legend('Location', 'southwest')
box on

% ylim([0 max(means(:)+stds(:))*1.05])
xlim([3 12])

% Make plot look nicer
set(gca,'FontSize', 12)
set(gca,'Box','off')

pos = [930   730   830   460];
set(fh,'Position',pos)

saveas(fh,[res_dir '/pressure_ratios.fig']);
saveas(fh,[res_dir '/pressure_ratios.png']);
saveas(fh,[res_dir '/pressure_ratios.svg']);
