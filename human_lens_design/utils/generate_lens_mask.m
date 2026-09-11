

% granularity_factor = 1 means no division (finest pillars)
% granularity_factor = 3 means original behavior (wider pillars)
% Higher values create even wider pillars

function lens_mask = generate_lens_mask(kgrid, pillar_width_mm, seed)
    granularity_factor = pillar_width_mm/(kgrid.dx * 1000);
    
    rng(seed);
    
    % Create a smaller random mask based on granularity factor
    small_Ny = ceil(kgrid.Ny/granularity_factor);
    small_Nz = ceil(kgrid.Nz/granularity_factor);
    small_mask = rand(small_Ny, small_Nz);
    
    % Expand to full size using nearest neighbor interpolation
    [small_y, small_z] = meshgrid(1:small_Ny, 1:small_Nz);
    full_y = linspace(1, small_Ny, kgrid.Ny);  % This ensures exact size
    full_z = linspace(1, small_Nz, kgrid.Nz);  % This ensures exact size
    [full_y, full_z] = meshgrid(full_y, full_z);
    
    % Interpolate
    lens_yz_mask = interp2(small_y, small_z, small_mask', full_y, full_z, 'nearest')';
    
    % Trim to exact size if needed
    lens_yz_mask = lens_yz_mask(1:kgrid.Ny, 1:kgrid.Nz);
    
    % Return the mask
    lens_mask = lens_yz_mask;
end