

function plotMask()
    % Create and show the mask
    figure;
    
    % Main mask visualization
    subplot(2,1,1);
    imagesc(lens_yz_mask);
    colorbar;
    title('Full Mask');
    axis image;
    
    % Zoomed section to see pixels clearly
    subplot(2,1,2);
    % Take a small section - let's say 15x15 pixels
    small_section = lens_yz_mask(1:15, 1:15);
    imagesc(small_section);
    colorbar;
    title('Zoomed View (15x15 pixels)');
    axis image;
    grid on;
    set(gca, 'GridColor', 'w');  % Make grid white
    % Add text to show values in each block
    [ny, nz] = size(small_section);
    for i = 1:ny
        for j = 1:nz
            text(j, i, sprintf('%.2f', small_section(i,j)), ...
                'HorizontalAlignment', 'center', ...
                'Color', 'w');
        end
    end
end