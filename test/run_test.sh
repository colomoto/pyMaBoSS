#!/bin/bash

return_code=0

check()
{
    if [ $? = 0 ]; then
    	echo "$1 OK"
    else
	    echo "$1 ERR"
        return_code=1
    fi
}

RUN_BINARY=${RUN_WITH:-python}

$RUN_BINARY -m unittest test.test_conversion
check "conversion"
$RUN_BINARY -m unittest test.test_loadmodels
check "loadmodels"
$RUN_BINARY -m unittest test.test_observed_graph
check "observed_graph"
$RUN_BINARY -m unittest test.test_pipelines
check "pipelines"
$RUN_BINARY -m unittest test.test_probtrajs
check "probtrajs"
$RUN_BINARY -m unittest test.test_statdist
check "statdist"
$RUN_BINARY -m unittest test.test_types
check "types"
$RUN_BINARY -m unittest test.test_uppmaboss
check "uppmaboss"
$RUN_BINARY -m unittest test.test_compute_logical
check "compute_logical"
$RUN_BINARY -m unittest test.test_evaluator
check "evaluator"
$RUN_BINARY -m unittest test.test_extractor
check "extractor"
$RUN_BINARY -m unittest test.test_parser
check "parser"

exit $return_code
