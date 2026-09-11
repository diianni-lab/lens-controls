function anatomy = loadAnatomy(caseConfig)

anatomy.ctFile = fullfile( ...
    caseConfig.dataRoot, caseConfig.ctFile);
anatomy.segmentationFile = fullfile( ...
    caseConfig.dataRoot, caseConfig.segmentationFile);

anatomy.ctInfo = niftiinfo(anatomy.ctFile);
anatomy.segmentationInfo = niftiinfo( ...
    anatomy.segmentationFile);

anatomy.ctHu = single(niftiread(anatomy.ctInfo));
anatomy.labels = single(niftiread( ...
    anatomy.segmentationInfo));

anatomy.ctGeometry = imageGeometry(anatomy.ctInfo);
anatomy.segmentationGeometry = imageGeometry( ...
    anatomy.segmentationInfo);
end

function geometry = imageGeometry(info)

geometry.size = double(info.ImageSize(1:3));
geometry.spacingM = ...
    1e-3 * double(info.PixelDimensions(1:3));
geometry.originM = ...
    1e-3 * double(info.Transform.T(4, 1:3));
end
