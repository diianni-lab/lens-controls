function result = run_human_case(caseId, dataRoot, outputRoot)

engineRoot = fileparts(mfilename('fullpath'));
configRoot = fullfile(engineRoot, 'configs', 'human');

simulationConfig = jsondecode(fileread( ...
    fullfile(configRoot, 'simulation.json')));
caseList = jsondecode(fileread( ...
    fullfile(configRoot, 'cases.json')));

caseIds = cellfun( ...
    @(item) item.caseId, ...
    caseList.cases, ...
    'UniformOutput', false);
caseConfig = caseList.cases{strcmp(caseIds, caseId)};

if isfield(caseConfig, 'gridSpacingM')
    simulationConfig.grid.spacingM = ...
        caseConfig.gridSpacingM;
end
if isfield(caseConfig, 'pmlSize')
    simulationConfig.solver.pmlSize = ...
        caseConfig.pmlSize;
end

caseConfig.dataRoot = dataRoot;
caseConfig.outputDir = fullfile(outputRoot, caseId);

result = engine.runCase("human", simulationConfig, caseConfig);
end
