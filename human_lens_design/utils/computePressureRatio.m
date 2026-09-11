function [avg_p_in,avg_p_out,p_ratio] = computePressureRatio(p, in_volume)
    % % Create an alphaShape object
    % shp = alphaShape(isosurface_handle.vertices,Inf);
    % 
    % points = [X(:), Y(:), Z(:)];
    % 
    % % Test which points are inside the alpha shape
    % in_volume = inShape(shp, points);
    % in_volume = reshape(in_volume, size(p));
    % 
    % figure; imagesc(squeeze(in_volume(:,:,round(size(p,3)/2))));
    % figure; imagesc(squeeze(p(:,:,round(size(p,3)/2))))

    % Calculate average pressures
    avg_p_in = mean(p(in_volume),'omitnan');
    avg_p_out = mean(p(~in_volume),'omitnan');

    p_ratio = avg_p_in/avg_p_out;
    
    fprintf('\nPressure Analysis:\n');
    fprintf('Average pressure inside: %.2e\n', avg_p_in);
    fprintf('Average pressure outside: %.2e\n', avg_p_out);
    fprintf('Ratio (inside/outside): %.2f\n', p_ratio);
end
