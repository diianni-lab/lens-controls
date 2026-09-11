
clearvars;
close all;
clc;

res_dir = './results/variable_thickness_and_pillar_widths/press_ratio_6dB';

load([res_dir '/pressure_ratios.mat']);

% Get unique values of thickness and pillar width
thicknesses = unique([results.thickness]);
pillar_widths = unique([results.pillar_width]);

% Initialize arrays to store means and standard deviations
means = zeros(length(thicknesses), length(pillar_widths));
stds = zeros(length(thicknesses), length(pillar_widths));

% Calculate means and standard deviations for each combination
for i = 1:length(thicknesses)
    for j = 1:length(pillar_widths)
        % Find all pressure ratios for this combination
        idx = [results.thickness] == thicknesses(i) & ...
              [results.pillar_width] == pillar_widths(j);
        ratios = [results(idx).pressure_ratio];
        
        means(i,j) = mean(ratios);
        stds(i,j) = std(ratios);
    end
end

% Create the plot
fh = figure(1);

hold on

plot(linspace(0,10,100),ones(1,100)*results_nolens.pressure_ratio,'k--',...
    'LineWidth',1.5,...
    'DisplayName', 'No lens');

% Plot each thickness as a separate line with error bars
% colors = lines(length(thicknesses));  % Get different colors for each line
% colors = slanCM('bold',8);
colors = slanCM('prism2',8);
for i = 1:length(thicknesses)
    errorbar(pillar_widths, means(i,:), stds(i,:), '-o', ...
        'Color', colors(i,:), ...
        'LineWidth', 1.5, ...
        'MarkerSize', 8, ...
        'MarkerFaceColor', colors(i,:), ...
        'DisplayName', [num2str(thicknesses(i)) ' mm']);
end

% Customize the plot
xlabel('Pillar Width', 'FontSize', 12)
ylabel('Pressure Ratio', 'FontSize', 12)
title(['Pressure Ratio at ' num2str(-db_drop) ' dB'], 'FontSize', 14)
% grid on
legend('Location', 'southwest')
box on

% ylim([0 max(means(:)+stds(:))*1.05])
xlim([0 10])

% Make plot look nicer
set(gca,'FontSize', 12)
set(gca,'Box','off')

pos = [930   730   830   460];
set(fh,'Position',pos)

saveas(fh,[res_dir '/pressure_ratios.fig']);
saveas(fh,[res_dir '/pressure_ratios.png']);
saveas(fh,[res_dir '/pressure_ratios.svg']);
