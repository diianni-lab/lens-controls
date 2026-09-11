function result = run_rat_case(caseId, dataRoot, outputRoot)

engineRoot = fileparts(mfilename('fullpath'));
configRoot = fullfile(engineRoot, 'configs', 'rat');

simulationConfig = jsondecode(fileread( ...
    fullfile(configRoot, 'simulation.json')));
caseList = jsondecode(fileread( ...
    fullfile(configRoot, 'cases.json')));

caseConfig = caseList.cases(strcmp( ...
    {caseList.cases.caseId}, caseId));

caseConfig.dataRoot = dataRoot;
caseConfig.outputDir = fullfile(outputRoot, caseId);

result = engine.runCase("rat", simulationConfig, caseConfig);
end
