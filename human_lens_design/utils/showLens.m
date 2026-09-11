function showLens(lens_mask, kgrid, diameters, x_ext, radius_of_curvature)
% Create transducer mask - one for each element
    transducer_masks = zeros(size(lens_mask,1), size(lens_mask,2), size(lens_mask,3), size(diameters,1));

    % Create a fine mesh for accurate curved surface
    [mesh_x, mesh_y, mesh_z] = meshgrid(kgrid.x_vec, kgrid.y_vec, kgrid.z_vec);
    
    % Position the center of the transducer
    center_x = -x_ext/2 + 10e-3;  % [m] position along x-axis
    center_y = 0;                 % [m] centered in y
    center_z = 0;                 % [m] centered in z

    transducer_thickness = 2e-3;  % [m] thickness of the transducer elements

    % Define colors for each element
    element_colors = [1 0 0;    % red
                     0 1 0;    % green
                     1 1 0;    % yellow
                     1 0 1];   % magenta

    % For each annular element
    for element = 1:size(diameters, 1)
        inner_radius = diameters(element, 1) / 2;
        outer_radius = diameters(element, 2) / 2;
        
        % Calculate radial distance from center axis for each point
        radial_dist = sqrt((mesh_y - center_y).^2 + (mesh_z - center_z).^2);
        
        % Calculate x position of curved surface for each radius
        % Using spherical cap equation: x = R - sqrt(R^2 - r^2)
        % where R is radius_of_curvature and r is radial distance
        x_surface = center_x + (radius_of_curvature - sqrt(radius_of_curvature^2 - radial_dist.^2));
        
        % Create mask for this annular element
        element_mask = (radial_dist >= inner_radius) & ...
                      (radial_dist <= outer_radius) & ...
                      (mesh_x >= x_surface) & ...
                      (mesh_x <= (x_surface + transducer_thickness));
        
        % Store mask for this element
        transducer_masks(:,:,:,element) = permute(element_mask, [2 1 3]);
    end

    % Visualization code
    figure;
    subplot(1,4,[1,2])
    % Original lens visualization
    imagesc(kgrid.z_vec*1e3, kgrid.x_vec*1e3, squeeze(lens_mask(:,floor(kgrid.Ny/2),:)))
    hold on
    % Add each transducer element in different color
    for element = 1:size(diameters, 1)
        transducer_slice_xz = squeeze(transducer_masks(:,floor(kgrid.Ny/2),:,element));
        [trans_x, trans_z] = find(transducer_slice_xz);
        if ~isempty(trans_x) && ~isempty(trans_z)
            scatter(kgrid.z_vec(trans_z)*1e3, kgrid.x_vec(trans_x)*1e3, 1, ...
                    element_colors(element,:), 'filled')
        end
    end
    xlabel('z [mm]')
    ylabel('x [mm]')
    title('XZ Plane View (Center Slice)')
    axis image
    
    % Plot 2: YZ plane view using high-resolution circles - larger subplot
    subplot(1,4,[3,4])
    hold on
    
    % Plot each annular element using high-resolution circles
    for element = 1:size(diameters, 1)
        inner_radius = diameters(element, 1) / 2;
        outer_radius = diameters(element, 2) / 2;
        
        % Create filled ring using patch
        theta = linspace(0, 2*pi, 200);
        inner_x = inner_radius * cos(theta);
        inner_y = inner_radius * sin(theta);
        outer_x = outer_radius * cos(theta);
        outer_y = outer_radius * sin(theta);
        
        % Combine inner and outer circles for patch
        x = [inner_x, fliplr(outer_x)];
        y = [inner_y, fliplr(outer_y)];
        
        % Plot filled ring
        patch(x*1e3, y*1e3, element_colors(element,:), 'FaceAlpha', 0.5)
    end
    
    xlabel('z [mm]')
    ylabel('y [mm]')
    title('YZ Plane View (Transducer Face)')
    axis image
    grid on
    
    % Set axis limits to show full transducer with margin
    max_diameter = max(diameters(:,2));
    plot_limit = ceil(max_diameter * 1000 * 0.6); % Increased margin
    xlim([-plot_limit plot_limit])
    ylim([-plot_limit plot_limit])
    
    % Add legend
    legend_elements = [];
    element_names = {};
    for i = 1:size(diameters,1)
        legend_elements(i) = patch(NaN, NaN, element_colors(i,:), 'FaceAlpha', 0.5);
        element_names{i} = sprintf('Element %d (%.1f-%.1f mm)', i, ...
                                  diameters(i,1)*1e3, diameters(i,2)*1e3);
    end
    legend(legend_elements, element_names, 'Location', 'southoutside')

end