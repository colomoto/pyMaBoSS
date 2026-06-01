echo off

if not defined RUN_WITH (
    set RUN_WITH=python
)
set /A FAIL=0

%RUN_WITH% -m unittest test.test_conversion
call:check

%RUN_WITH% -m unittest test.test_loadmodels
call:check

%RUN_WITH% -m unittest test.test_observed_graph
call:check

%RUN_WITH% -m unittest test.test_pipelines
call:check

%RUN_WITH% -m unittest test.test_probtrajs
call:check

%RUN_WITH% -m unittest test.test_statdist
call:check

%RUN_WITH% -m unittest test.test_types
call:check

%RUN_WITH% -m unittest test.test_uppmaboss
call:check

%RUN_WITH% -m unittest test.test_compute_logical
call:check

%RUN_WITH% -m unittest test.test_evaluator
call:check

%RUN_WITH% -m unittest test.test_extractor
call:check

%RUN_WITH% -m unittest test.test_parser
call:check

exit /b %FAIL%



:check 
if %ERRORLEVEL% NEQ 0 (
    set /A FAIL=1
)
exit /b 