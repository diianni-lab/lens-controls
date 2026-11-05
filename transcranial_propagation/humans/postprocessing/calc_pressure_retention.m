clear all;
close all;
clc;


% load brain data
brain = readtable('./brain/summary.csv');

p_lens_target = brain.insideMeanKPa(strcmp(brain.condition,'lens'));
p_active_target = brain.insideMeanKPa(strcmp(brain.condition,'nolens'));

ratio_lens_target = brain.insideOutsideMeanRatio(strcmp(brain.condition,'lens'));
ratio_active_target = brain.insideOutsideMeanRatio(strcmp(brain.condition,'nolens'));

% load skull data
skull = readtable('./skull/summary.csv');

p_lens_skull = skull.skullMeanKPa(strcmp(skull.condition,'lens'));
p_active_skull = skull.skullMeanKPa(strcmp(skull.condition,'nolens'));

%% calc pressure retention at the target

p_retention_target = p_lens_target./p_active_target;

disp(['Mean pressure retention at target: mean = ' num2str(mean(p_retention_target)*100)]);
disp(['Mean pressure retention at target: std = ' num2str(std(p_retention_target)*100)]);
disp(' ');

%% calc pressure decrease at the target

p_decrease_target = (p_active_target-p_lens_target)./p_active_target;

disp(['Mean pressure decrease at target: mean = ' num2str(mean(p_decrease_target)*100)]);
disp(['Mean pressure decrease at target: std = ' num2str(std(p_decrease_target)*100)]);
disp(' ');

%% calc ratio retention at the target

ratio_target = ratio_lens_target./ratio_active_target;

disp(['Mean pressure ratio retention at target: mean = ' num2str(mean(ratio_target)*100)]);
disp(['Mean pressure ratio retention at target: std = ' num2str(std(ratio_target)*100)]);
disp(' ');

%% calc ratio decrease at the target

ratio_decrease_target = (ratio_active_target-ratio_lens_target)./ratio_active_target;

disp(['Mean pressure ratio decrease at target: mean = ' num2str(mean(ratio_decrease_target)*100)]);
disp(['Mean pressure ratio decrease at target: std = ' num2str(std(ratio_decrease_target)*100)]);
disp(' ');

%% calc pressure retention in the skull

p_retention_skull = p_lens_skull./p_active_skull;

disp(['Mean pressure retention in skull: mean = ' num2str(mean(p_retention_skull)*100)]);
disp(['Mean pressure retention in skull: std = ' num2str(std(p_retention_skull)*100)]);
disp(' ');
