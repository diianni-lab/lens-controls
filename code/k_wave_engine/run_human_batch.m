function results = run_human_batch(dataRoot, outputRoot)

engineRoot = fileparts(mfilename('fullpath'));
caseList = jsondecode(fileread( ...
    fullfile(engineRoot, 'configs', 'human', 'cases.json')));

numCases = numel(caseList.cases);
results = cell(numCases, 1);

for caseIndex = 1:numCases
    caseId = caseList.cases{caseIndex}.caseId;
    fprintf('[%d/%d] %s\n', caseIndex, numCases, caseId);

    results{caseIndex} = run_human_case( ...
        caseId, dataRoot, outputRoot);
end
end
