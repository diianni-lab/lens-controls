

% granularity_factor = 1 means no division (finest pillars)
% granularity_factor = 3 means original behavior (wider pillars)
% Higher values create even wider pillars

function mask_xy = generate_lens_mask_xy(kgrid, pillar_width_mm, seed)
    % pillar granularity measured in grid steps along x and y
    gran_x = pillar_width_mm / (kgrid.dx * 1000);    % cells per pillar (x)
    gran_y = pillar_width_mm / (kgrid.dy * 1000);    % cells per pillar (y)

    rng(seed);
    
    % Create a smaller random mask based on granularity factor
    small_Nx = ceil(kgrid.Nx / max(gran_x, 1e-6));
    small_Ny = ceil(kgrid.Ny / max(gran_y, 1e-6));
    small_mask = rand(small_Nx, small_Ny);

    % Expand to full size using nearest neighbor interpolation
    [sx, sy] = meshgrid(1:small_Nx, 1:small_Ny);
    full_x = linspace(1, small_Nx, kgrid.Nx);
    full_y = linspace(1, small_Ny, kgrid.Ny);
    [fx, fy] = meshgrid(full_x, full_y);
    mask_xy = interp2(sx, sy, small_mask.', fx, fy, 'nearest').';  % Nx x Ny
    mask_xy = mask_xy(1:kgrid.Nx, 1:kgrid.Ny);                     % exact size
end
