
clearvars;
close all;
clc;

res_dir = './results/variable_focus_9mm_lens_pillar_width_7/press_ratio_6dB';

load([res_dir '/pressure_ratios.mat']);

thickness = 11;
pillar_width = 9;

% Get unique values of focal length
focal_length = unique([results.focal_length]);

% Initialize arrays to store means and standard deviations
means = zeros(length(focal_length),1);
stds = zeros(length(focal_length),1);

% Calculate means and standard deviations for each combination
for k = 1:length(focal_length)

    no_lens(k) = results_nolens(k).pressure_ratio;

    idx = [results.focal_length] == focal_length(k);
    
    ratios = [results(idx).pressure_ratio];
    
    means(k) = mean(ratios);
    stds(k) = std(ratios);
end

% Create the plot
fh = figure();

hold on

plot(focal_length,no_lens,'b',...
    'LineWidth',1.5,...
    'DisplayName', 'No lens');

errorbar(focal_length, means, stds, '-o', ...
        'Color','red', ...
        'LineWidth', 1.5, ...
        'MarkerSize', 8, ...
        'DisplayName', 'Lens');

% Customize the plot
xlabel('Focal length (mm)', 'FontSize', 12)
ylabel('Pressure ratio', 'FontSize', 12)
title(['Pressure ratio at ' num2str(-db_drop) ' dB'], 'FontSize', 14)
% grid on
legend('Location', 'southwest')
box on

% ylim([0 max(means(:)+stds(:))*1.05])
% xlim([0 10])

% Make plot look nicer
set(gca,'FontSize', 12)
set(gca,'Box','off')

% pos = [930   730   830   460];
% set(fh,'Position',pos)

saveas(fh,[res_dir '/pressure_ratios.fig']);
saveas(fh,[res_dir '/pressure_ratios.png']);
saveas(fh,[res_dir '/pressure_ratios.svg']);
