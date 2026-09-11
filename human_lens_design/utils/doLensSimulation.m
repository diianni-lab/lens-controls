
function doLensSimulation(basefilename, subFolder, seed, use_lens, use_inverted_lens, lens_thickness_mm, pillar_width_mm, use_delays, focal_length_mm, amp_comp, x_ext)

close all

% convert focal length and thickness
focal_length = focal_length_mm/1000;
lens_thickness = lens_thickness_mm/1000;

if use_lens
    if use_inverted_lens
        inverted_text =  'inverted_lens';
    else 
        inverted_text =  'lens';
    end
    lens_text = [num2str(lens_thickness_mm), 'mm_', inverted_text,'_pillar_width_',  num2str(pillar_width_mm)];    
else
    lens_text =  'no_lens';
end

if use_delays
    delays_text = ['_focus_' num2str(focal_length_mm)];
else
    delays_text = '';
end

filename = [basefilename, lens_text, delays_text, '_seed_', num2str(seed)];

% simulation settings
DATA_CAST = 'gpuArray-single';
%DATA_CAST = 'single';

% % transducer properties
% Transducer geometry
radius_of_curvature = 150e-3;    % Radius of curvature of the bowl [m]
% Ring diameters (from innermost to outermost)
diameters= [5.2e-3, 31.4e-3; 31.4e-3, 44.4e-3; 44.4e-3, 54.3e-3; 54.3e-3, 62.6e-3];

% =========================================================================
% DEFINE GRID
% =========================================================================

% define the extension of the simulation grid [m]
y_ext = 90e-3;   
z_ext = 90e-3;

% define grid point spacing [m]
dx = 0.5e-3;   % [m] Increased from 0.2mm to 0.5mm
dy = dx;       % [m]
dz = dx;       % [m]

% define the PML size 
PML_X_SIZE = 20;           % [grid points] 
PML_Y_SIZE = 10;           % [grid points] 
PML_Z_SIZE = 10;           % [grid points]

% define the grid parameters - ensure odd number of points
Nx = floor(x_ext/dx/2)*2+1 - 2*PML_X_SIZE;    % [grid points]
Ny = floor(y_ext/dy/2)*2+1 - 2*PML_Y_SIZE;    % [grid points]
Nz = floor(z_ext/dz/2)*2+1 - 2*PML_Z_SIZE;    % [grid points]

% create the computational grid
kgrid = kWaveGrid(Nx, dx, Ny, dy, Nz, dz);

% =========================================================================
% DEFINE MEDIUM
% =========================================================================

% define medium - sound speed and density - values from Aubry 2022
c_water = 1500;
d_water = 1000;

medium.sound_speed = ones(size(kgrid.x))*c_water;      % [m/s]
medium.density = ones(size(kgrid.x))*d_water;      % [kg/m^3]

% define medium - attenuation
medium.alpha_power = 1.001;

att_water = 0;
medium.alpha_coeff = ones(size(kgrid.x))*att_water;

medium.alpha_mode = 'no_dispersion';

if use_lens
    % aberrating lens
    % Initialize lens mask with same size as medium
    lens_mask = zeros(size(kgrid.x));
    
    if pillar_width_mm>0
        % Create random mask for YZ plane with pillars sized according to the granularity_factor
        lens_yz_mask = generate_lens_mask(kgrid, pillar_width_mm, seed);
    else
        lens_yz_mask = ones(kgrid.Ny,kgrid.Nz);
    end
    
    % Position and thickness parameters
    % lens_x_pos_kgrid = -x_ext/2 + 30e-3; % -60e-3;  % [m] - position of medium side
    lens_xdcr_dist = 3e-3;  % lens distance from edge of transducer
    lens_x_pos_kgrid = kgrid.x_vec(1)+5e-3+lens_xdcr_dist+lens_thickness;
    base_thickness = 2e-3;      % [m]
    var_thickness = lens_thickness - base_thickness;       % [m]
    
    % Create lens
    for ky = 1:kgrid.Ny
        for kz = 1:kgrid.Nz
            % Calculate thickness for this y,z position
            thickness_yz = base_thickness + var_thickness * lens_yz_mask(ky,kz);
            
            % Find x indices for this thickness
            if use_inverted_lens
                % for inverted lens, pillars exist between 
                % lens_x - lens_thickness and lens_x - lens_thickness + thickness_yz
                x_idx = find(kgrid.x_vec >= lens_x_pos_kgrid - lens_thickness & ...
                            kgrid.x_vec <= (lens_x_pos_kgrid - lens_thickness + thickness_yz));
            else
                % for non-inverted pillars exist between lens_x - thickness and lens_x
                x_idx = find(kgrid.x_vec >= (lens_x_pos_kgrid - thickness_yz) ...
                    & kgrid.x_vec <= lens_x_pos_kgrid);
            end
            
            % Set mask to 1 for these positions
            lens_mask(x_idx,ky,kz) = 1;
        end
    end

    showLens(lens_mask, kgrid, diameters, x_ext, radius_of_curvature)

    % values from Jimenez-Gambin, Physical Review Applied, 2020
    medium.sound_speed(find(lens_mask)) = 2580;     % [m/s]
    medium.density(find(lens_mask)) = 1171;         % [kg/m^3]
    medium.alpha_coeff(find(lens_mask)) = 1.38*2;   % power law absorption coefficient [dB/(MHz^y cm)]
end

% Visualization of medium properties
figure;
imagesc(kgrid.y_vec*1e3,kgrid.x_vec*1e3,squeeze(medium.sound_speed(:,:,round(Nz/2))));
axis image
xlabel('y (mm)')
ylabel('x (mm)')
title('kgrid coordinates - XY')

figure;
imagesc(kgrid.y_vec*1e3,kgrid.z_vec*1e3,squeeze(medium.sound_speed(25,:,:)));
axis image
xlabel('y (mm)')
ylabel('z (mm)')
title('kgrid coordinates - YZ')

figure;
imagesc(kgrid.z_vec*1e3,kgrid.x_vec*1e3,squeeze(medium.sound_speed(:,round(Ny/2),:)));
axis image
xlabel('z (mm)')
ylabel('x (mm)')
title('kgrid coordinates - XZ')

% =========================================================================
% DEFINE INPUT SIGNAL
% =========================================================================

% define properties of the input signal
source_amp = 0.0832*1e6; % calibrated to give 1 MPa at 80 mm

if use_lens
    source_amp = source_amp*(1+amp_comp);
end

tone_burst_freq = 5e5;        % [Hz] Keeping same frequency
tone_burst_cycles = x_ext/2e-3 + 10;

% create the time array
kgrid.makeTime(medium.sound_speed,[], 0.6 * tone_burst_cycles/tone_burst_freq);

% create input signal
input_signal = source_amp * sin(2 * pi * tone_burst_freq * (0:kgrid.dt:tone_burst_cycles/tone_burst_freq));

% apply tukey window to input signal
input_signal = input_signal.*tukeywin(length(input_signal),0.1)';


% =========================================================================
% DEFINE TRANSDUCER
% =========================================================================

karray = kWaveArray;

num_elements = size(diameters, 1);
delayed_signals = zeros(num_elements, length(input_signal));

if use_delays
    delays = calculateTransducerDelays(radius_of_curvature, focal_length, diameters, c_water);
    
    %%calculate delayed signals for the different elements  
    % get longest delay
    longest_delay = max(delays);
    
    % delay closer rings so that waves arrive at the same time
    % the smallest ring is closest to the focus so this one needs the maximum delay
    % subtract each time delay from the longest delay
    for n = 1:num_elements
        % Calculate time shift in samples
        shift_samples = round((longest_delay - delays(n)) / kgrid.dt);
        
        % Create delayed signal
        delayed_signal = zeros(size(input_signal));
        delayed_signal((shift_samples + 1):end) = input_signal(1:(end-shift_samples));
        delayed_signals(n, :) = delayed_signal;
    end    
else
    delayed_signals = repmat(input_signal, num_elements, 1);
end
 
% diameters= [5.2e-3, 31.4e-3; 31.4e-3, 44.4e-3; 44.4e-3, 54.3e-3; 54.3e-3, 62.6e-3];
% transducer_xpos = -x_ext/2 + 10e-3;
transducer_xpos = kgrid.x_vec(1);
position = [transducer_xpos, 0, 0];
focus = [0, 0, 0]; % set on the beam axis

karray.addAnnularArray(position, radius_of_curvature, diameters', focus);

% for n = 1:num_elements
%     karray.addAnnularElement(position, radius_of_curvature, diameters(n,:), focus)
% end

% assign binary mask from karray to the source mask
source.p_mask = karray.getArrayBinaryMask(kgrid);


% get distributed source signals (this automatically returns a weighted
% source signal for each grid point that forms part of the source)
source.p = karray.getDistributedSourceSignal(kgrid, delayed_signals);

% =========================================================================
% DEFINE SENSOR 
% =========================================================================

%sensor.record = {'p_min_all','p_max_all','p'};
sensor.record = {'p_min_all', 'p_max_all'};
sensor.mask = ones(Nx, Ny, Nz);

% =========================================================================
% RUN SIMULATION
% =========================================================================

% set the input settings
input_args = {'DisplayMask', 'off', ...
    'PMLInside', false, 'PlotPML', false, 'PMLSize', [PML_X_SIZE, PML_Y_SIZE, PML_Z_SIZE], ...
    'DataCast', DATA_CAST, 'PlotScale', 1/2*[-1, 1] * source_amp};

% Get the total number of sensor points
sensor_indices = find(sensor.mask); % Linear indices of sensor points
M = length(sensor_indices);

% Run the simulation for the current batch
[sensor_data] = kspaceFirstOrder3D(kgrid, medium, source, sensor, input_args{:});

% Store the matrix (pressure data) in the cell array
p_min_all = gather(sensor_data.p_min_all);
% Store the matrix (pressure data) in the cell array
p_max_all = gather(sensor_data.p_max_all);

if ~exist(subFolder, 'dir')
    mkdir(subFolder);
end

% fullpath = fullfile(subFolder, filename);
fullpath = [subFolder '/' filename '.mat'];

save(fullpath, "p_max_all", "p_min_all",'kgrid');

if use_lens
    save(fullpath,'lens_mask','-append');
end

% =========================================================================
% PLOTS
% =========================================================================

Z = 1.55e6;
I_sppa_factor = 1/(2*Z*1e4);

% plot pressure in coronal plane at the AP focal position
coron_plane_z_kgrid = 0;
[~,coron_plane_z_kgrid_idx] = min(abs(kgrid.z_vec-coron_plane_z_kgrid));

press_beam_plot_xy = -squeeze(p_min_all(:,:,coron_plane_z_kgrid_idx));

fh = figure;
imagesc(kgrid.y_vec*1e3,kgrid.x_vec*1e3,press_beam_plot_xy);
axis image;
xlabel('y (mm)');
ylabel('x (mm)');
colorbar;
title('Pressure Field')

clim([0 1e6])

saveas(fh, [fullpath, + '.fig']);
saveas(fh, [fullpath, + '.png']);

% close all;
% clc;

end
