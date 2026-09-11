
% function calculateTransducerDelays() computes the distance of each
% element from the focus and the delays to the more distant elements
% radius_of_curvature - radius of curvature of the transducer [m]
% focal_length - steering depth
% daimeters of the transducer elements
function delays = calculateTransducerDelays(radius_of_curvature, focal_length, diameters, speed_of_sound)

    num_elements = size(diameters, 1);
    
    ring_diameters = zeros(num_elements, 1);
    
    for n = 1:num_elements
        % get average diameter
        ring_diameters(n) = (diameters(n,2) + diameters(n,1))/2;
    end
        
    % Calculate ring radii (distance from center axis)
    ring_radii = ring_diameters / 2;
    
    % Calculate the z-position (depth) of each ring
    z_positions = zeros(1, 4);
    for i = 1:4
        % Using pythagorean theorem: R^2 = r^2 + (R-z)^2
        % where R is radius of curvature, r is ring radius, z is depth
        z_positions(i) = radius_of_curvature - sqrt(radius_of_curvature^2 - ring_radii(i)^2);
    end
    
    % Calculate path length from each ring to focal point
    path_lengths = zeros(1, 4);
    for i = 1:4
        % Distance formula in cylindrical coordinates
        path_lengths(i) = sqrt(ring_radii(i)^2 + (focal_length - z_positions(i))^2);
    end
    
    % Calculate delays relative to innermost ring (shortest path)
    delays = (path_lengths - min(path_lengths)) / speed_of_sound;

    %delays = zeros(1, 4);
    
    % Plot the transducer geometry
    figure;
    hold on;
    grid on;
    axis equal;
    
    % Plot bowl profile
    theta = linspace(-asin(max(ring_diameters)/2/radius_of_curvature), ...
                     asin(max(ring_diameters)/2/radius_of_curvature), 100);
    x_bowl = radius_of_curvature * sin(theta);
    z_bowl = radius_of_curvature * (1 - cos(theta));  % Changed sign
    bowl_line = plot(x_bowl*1000, -1 + z_bowl*1000, 'r--', 'LineWidth', 1);
    
    % Plot rings
    for i = 1:4
        x = [-diameters(i,2)/2, -diameters(i,1)/2];
        z = [z_positions(i), z_positions(i)];
        ring_lines(1) = plot(x*1000, z*1000, 'b-', 'LineWidth', 2);

        x = [diameters(i,2)/2, diameters(i,1)/2];
        z = [z_positions(i), z_positions(i)];
        ring_lines(1) = plot(x*1000, z*1000, 'b-', 'LineWidth', 2);
    end
    
    % Plot focal point
    focal_point = plot(0, focal_length*1000, 'r*', 'MarkerSize', 10);
    ylim([-10, focal_length*1000 + 10]);
    %plot(0, radius_of_curvature*1000, 'b*', 'MarkerSize', 10);
    %ylim([0, radius_of_curvature*1000 + 10]);
    
    xlabel('Radial position (mm)');
    ylabel('Axial position (mm)');
    title('Transducer Geometry');
    legend([bowl_line, ring_lines(1), focal_point], {'Bowl profile', 'Ring elements', 'Focal point'});
    
    % Display results
    disp('Ring properties:')
    for i = 1:4
        fprintf('Ring %d:\n', i);
        fprintf('  Diameter: %.2f mm\n', ring_diameters(i)*1000);
        fprintf('  Z-position: %.2f mm\n', z_positions(i)*1000);
        fprintf('  Path length: %.2f mm\n', path_lengths(i)*1000);
        fprintf('  Delay: %.2f µs\n\n', delays(i)*1e6);
    end

end