function anatomy = loadAnatomy(caseConfig)

anatomy.anatomyFile = fullfile( ...
    caseConfig.dataRoot, caseConfig.anatomyFile);

data = load(anatomy.anatomyFile);

anatomy.ctHu = single(data.ct_data_hu);
anatomy.labels = zeros(size(anatomy.ctHu), 'single');
anatomy.labels(data.ct_brain ~= 0) = 1;
anatomy.labels(data.ct_bone ~= 0) = 2;

geometry = volumeGeometry(data);
anatomy.ctGeometry = geometry;
anatomy.segmentationGeometry = geometry;
end

function geometry = volumeGeometry(data)

geometry.size = double(size(data.ct_data_hu));
geometry.spacingM = double([ ...
    data.x_axis(2) - data.x_axis(1), ...
    data.y_axis(2) - data.y_axis(1), ...
    data.z_axis(2) - data.z_axis(1)]);
geometry.originM = double([ ...
    data.x_axis(1), ...
    data.y_axis(1), ...
    data.z_axis(1)]);
end
