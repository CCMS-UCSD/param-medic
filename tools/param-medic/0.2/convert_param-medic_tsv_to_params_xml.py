#!/usr/bin/python

import sys
import getopt
import csv
from xml.etree.ElementTree import Element, SubElement, tostring

# default params.xml parameters
DEFAULT_PRECURSOR_MASS_TOLERANCE_PARAMETER = "tolerance.PM_tolerance"
DEFAULT_PRECURSOR_MASS_TOLERANCE_UNITS_PARAMETER = "tolerance_unit.PM_unit"
DEFAULT_FRAGMENT_TOLERANCE_PARAMETER = "tolerance.Ion_tolerance"
DEFAULT_PHOSPHO_PARAMETER = "ptm.PHOSPHORYLATION"
DEFAULT_ITRAQ_8PLEX_K_PARAMETER = "ptm.ITRAQ_8PLEX_K"
DEFAULT_ITRAQ_8PLEX_NTERM_PARAMETER = "ptm.ITRAQ_8PLEX_NTERM"
DEFAULT_CUSTOM_MOD_PARAMETER = "ptm.custom_PTM"
# params.xml custom modification parameter values
SILAC_4DA_PARAMETER_VALUE = "+4.025107,RK,opt"
SILAC_6DA_PARAMETER_VALUE = "+6.020129,RK,opt"
SILAC_8DA_PARAMETER_VALUE = "+8.014199,K,opt"
SILAC_10DA_PARAMETER_VALUE = "+10.008269,R,opt"
ITRAQ_4PLEX_K_PARAMETER_VALUE = "+144.10253,K,fix"
ITRAQ_4PLEX_NTERM_PARAMETER_VALUE = "+144.10253,*,fix_nterm"
TMT_2PLEX_K_PARAMETER_VALUE = "+225.155833,K,fix"
TMT_2PLEX_NTERM_PARAMETER_VALUE = "+225.155833,*,fix_nterm"
TMT_6PLEX_K_PARAMETER_VALUE = "+229.162932,K,fix"
TMT_6PLEX_NTERM_PARAMETER_VALUE = "+229.162932,*,fix_nterm"
PHOSPHORYLATION_PARAMETER_VALUE = "+79.966331,STY,opt"
# expected Param-Medic TSV column names
PARAM_MEDIC_COLUMNS = {}
PARAM_MEDIC_COLUMNS["PRECURSOR_MASS_TOLERANCE"] = "precursor_prediction_ppm"
PARAM_MEDIC_COLUMNS["FRAGMENT_TOLERANCE"] = "fragment_prediction_th"
PARAM_MEDIC_COLUMNS["SILAC_4DA"] = "SILAC_4Da_present"
PARAM_MEDIC_COLUMNS["SILAC_6DA"] = "SILAC_6Da_present"
PARAM_MEDIC_COLUMNS["SILAC_8DA"] = "SILAC_8Da_present"
PARAM_MEDIC_COLUMNS["SILAC_10DA"] = "SILAC_10Da_present"
PARAM_MEDIC_COLUMNS["ITRAQ_4PLEX"] = "iTRAQ_4plex_present"
PARAM_MEDIC_COLUMNS["ITRAQ_8PLEX"] = "iTRAQ_8plex_present"
PARAM_MEDIC_COLUMNS["TMT_2PLEX"] = "TMT_2plex_present"
PARAM_MEDIC_COLUMNS["TMT_6PLEX"] = "TMT_6plex_present"
PARAM_MEDIC_COLUMNS["PHOSPHORYLATION"] = "phospho_present"

def usage():
    print("python convert_param-medic_tsv_to_params_xml.py <Param-Medic_TSV_input_file> <params.xml_snippet_output_file> [-p <precursor_mass_tolerance_parameter_name>] [-u <precursor_mass_tolerance_units_parameter_name>] [-f <fragment_tolerance_parameter_name>] [-m <custom_PTM_parameter_name>]")

def main():
    if len(sys.argv) < 3:
        usage()
        sys.exit(1)
    tsv_filename = sys.argv[1]
    params_xml_filename = sys.argv[2]
    pmt_parameter = DEFAULT_PRECURSOR_MASS_TOLERANCE_PARAMETER
    pmt_units_parameter = DEFAULT_PRECURSOR_MASS_TOLERANCE_UNITS_PARAMETER
    ft_parameter = DEFAULT_FRAGMENT_TOLERANCE_PARAMETER
    phospho_parameter = DEFAULT_PHOSPHO_PARAMETER
    itraq_8_k_parameter = DEFAULT_ITRAQ_8PLEX_K_PARAMETER
    itraq_8_nterm_parameter = DEFAULT_ITRAQ_8PLEX_NTERM_PARAMETER
    mod_parameter = DEFAULT_CUSTOM_MOD_PARAMETER
    try:
        opts, args = getopt.getopt(sys.argv[3:],"p:u:f:m:")
    except getopt.GetoptError:
        usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt == "-p":
            pmt_parameter = arg
        elif opt == "-u":
            pmt_units_parameter = arg
        elif opt == "-f":
            ft_parameter = arg
        elif opt == "-m":
            mod_parameter = arg
    # read input TSV file
    pmt = None
    ft = None
    itraq_8_k = None
    itraq_8_nterm = None
    phospho = None
    mods = []
    columns = None
    with open(tsv_filename, "r") as tsv_file_reader:
        for line in csv.reader(tsv_file_reader, dialect="excel-tab"):
            # parse header
            if columns is None:
                columns = {}
                for i, column in enumerate(line):
                    for expected_column in PARAM_MEDIC_COLUMNS:
                        if column == PARAM_MEDIC_COLUMNS[expected_column]:
                            columns[i] = expected_column
                            break
            # parse row
            else:
                for i, value in enumerate(line):
                    if i in columns:
                        column = columns[i]
                        if column == "PRECURSOR_MASS_TOLERANCE":
                            pmt = value
                        elif column == "FRAGMENT_TOLERANCE":
                            ft = value
                        elif column == "SILAC_4DA" and value == "T":
                            mods.append(SILAC_4DA_PARAMETER_VALUE)
                        elif column == "SILAC_6DA" and value == "T":
                            mods.append(SILAC_6DA_PARAMETER_VALUE)
                        elif column == "SILAC_8DA" and value == "T":
                            mods.append(SILAC_8DA_PARAMETER_VALUE)
                        elif column == "SILAC_10DA" and value == "T":
                            mods.append(SILAC_10DA_PARAMETER_VALUE)
                        elif column == "ITRAQ_4PLEX" and value == "T":
                            mods.append(ITRAQ_4PLEX_K_PARAMETER_VALUE)
                            mods.append(ITRAQ_4PLEX_NTERM_PARAMETER_VALUE)
                        elif column == "ITRAQ_8PLEX" and value == "T":
                            itraq_8_k = "on"
                            itraq_8_nterm = "on"
                        elif column == "TMT_2PLEX" and value == "T":
                            mods.append(TMT_2PLEX_K_PARAMETER_VALUE)
                            mods.append(TMT_2PLEX_NTERM_PARAMETER_VALUE)
                        elif column == "TMT_6PLEX" and value == "T":
                            mods.append(TMT_6PLEX_K_PARAMETER_VALUE)
                            mods.append(TMT_6PLEX_NTERM_PARAMETER_VALUE)
                        elif column == "PHOSPHORYLATION" and value == "T":
                            phospho = "on"
    # build params.xml document
    document = Element("parameters")
    if pmt is not None:
        parameter = SubElement(document, "parameter", {"name":pmt_parameter})
        parameter.text = pmt
        parameter = SubElement(document, "parameter", {"name":pmt_units_parameter})
        parameter.text = "ppm"
    if ft is not None:
        parameter = SubElement(document, "parameter", {"name":ft_parameter})
        parameter.text = ft
    if itraq_8_k == "on":
        parameter = SubElement(document, "parameter", {"name":itraq_8_k_parameter})
        parameter.text = itraq_8_k
    if itraq_8_nterm == "on":
        parameter = SubElement(document, "parameter", {"name":itraq_8_nterm_parameter})
        parameter.text = itraq_8_nterm
    if phospho == "on":
        parameter = SubElement(document, "parameter", {"name":phospho_parameter})
        parameter.text = phospho
    for mod in mods:
        parameter = SubElement(document, "parameter", {"name":mod_parameter})
        parameter.text = mod
    # write params.xml document to output file
    with open(params_xml_filename, "w") as params_xml_file_writer:
        params_xml_file_writer.write(tostring(document, "utf-8"))

if __name__ == "__main__":
    main()
