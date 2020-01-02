/*
A KBase module: kb_metabolic
*/

module kb_metabolic {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    funcdef run_kb_metabolic(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

};
