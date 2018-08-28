#!/usr/bin/python

import os
import shutil
import subprocess
import sys

MSCONVERT_PATH = "/data/beta-proteomics2/tools/conversion_for_workflows/1/msconvert"
PARAM_MEDIC_PATH = "/opt/python-2.7.3/bin/param-medic"

def usage():
    print("python param-medic_wrapper.py <mzML_file> [<output_file>]")

def run_param_medic(input_filename, parameter_values):
    # if input file is not already mzML, convert it
    scratch_directory = None
    mzML_filename = input_filename
    path, extension = os.path.splitext(input_filename)
    if extension is None or extension.lower() != ".mzml":
        scratch_directory = os.path.join(os.getcwd(), "temp")
        if not os.path.exists(scratch_directory):
            os.mkdir(scratch_directory)
        mzML_filename = os.path.join(scratch_directory, os.path.basename(path) + ".mzML")
        msconvert_command = [MSCONVERT_PATH, input_filename, "--32", "--mzML", "-o", scratch_directory, "--outfile", os.path.basename(mzML_filename)]
        msconvert_output = None
        print "Calling msconvert:"
        print " ".join(msconvert_command)
        try:
            msconvert_output = subprocess.check_output(msconvert_command)
        except subprocess.CalledProcessError as error:
            print "msconvert failed with exit code " + str(error.returncode)
        if msconvert_output:
            print "msconvert output:"
            print "----------"
            print msconvert_output
            print "----------"
    # run Param-Medic, capture stdout
    parammedic_command = [PARAM_MEDIC_PATH]
    if parameter_values:
        for parameter, value in parameter_values.iteritems():
            parammedic_command.append("-" + parameter)
            parammedic_command.append(value)
    parammedic_command.append(mzML_filename)
    parammedic_output = None
    print "Calling Param-Medic:"
    print " ".join(parammedic_command)
    try:
        parammedic_output = subprocess.check_output(parammedic_command)
    except subprocess.CalledProcessError as error:
        print "Param-Medic failed with exit code " + str(error.returncode)
    # if Param-Medic call was successful, parse output for TSV log content
    header = None
    row = None
    if parammedic_output:
        print "Param-Medic output:"
        print "----------"
        print parammedic_output
        print "----------"
        in_tsv_section = False
        for line in parammedic_output.splitlines():
            # extract header line, minus the first token ("file" column)
            if line.startswith("file"):
                header = line.split("\t", 1)[1]
                in_tsv_section = True
            # extract the TSV data row, minus the first token ("file" column)
            elif in_tsv_section:
                row = line.split("\t", 1)[1]
    # if a scratch file was created, delete it
    if scratch_directory:
        shutil.rmtree(scratch_directory)
    return header, row

def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    # retrieve and validate input file
    input_filename = sys.argv[1]
    if not os.path.isfile(input_filename):
        print "Input file [" + input_filename + "] is not a readable file."
        sys.exit(1)
    # retrieve output and log files, if specified
    output_filename = None
    if len(sys.argv) > 2:
        output_filename = os.path.join(sys.argv[2], os.path.splitext(os.path.basename(input_filename))[0] + ".log")
    log_filename = "N/A"
    if len(sys.argv) > 3:
        log_filename = sys.argv[3]
    # retrieve and validate bypass flag
    false_values = ["false", "0", "no", "off"]
    run = True
    if len(sys.argv) > 4:
        if sys.argv[4].lower() in false_values:
            run = False
    # if the bypass flag was set, do nothing
    if run == False:
        # ensure the output file is created, if specified
        if output_filename:
            open(output_filename, "a").close()
        sys.exit(0)
    # retrieve remaining Param-Medic command line parameters
    param_medic_parameters = [
        "-min-precursor-mz",
        "-max-precursor-mz",
        "-min-frag-mz",
        "-max-frag-mz",
        "-max-precursor-delta-ppm",
        "-charges",
        "-max-scan-separation",
        "-min-peak-pairs",
        "-min-scan-frag-peaks",
        "-top-n-frag-peaks",
        "-min-common-frag-peaks",
        "-pair-top-n-frag-peaks"
    ]
    parameter_values = {}
    for i in range(5, len(sys.argv)):
        parameter = sys.argv[i]
        if sys.argv[i] in param_medic_parameters:
            parameter_values[sys.argv[i]] = sys.argv[i+1]
        else:
            continue
    # call Param-Medic on the indicated input file
    header, row = run_param_medic(input_filename, parameter_values)
    # if specified, write output to log file
    if output_filename:
        print "----------"
        try:
            output_file = open(output_filename, "w+")
            output_file.write("filename\tstatus")
            if header is not None:
                output_file.write("\t" + header)
            output_file.write("\tlog\n")
            output_file.write(os.path.basename(input_filename) + "\t")
            if row is not None:
                output_file.write("DONE\t" + row)
            else:
                output_file.write("FAILED")
            output_file.write("\t" + log_filename)
            output_file.close()
            print "Wrote Param-Medic TSV output to log file [", output_filename, "]"
        except:
            print "There was an error writing Param-Medic output to log file [", output_filename, "]"
            sys.exit(1)
    elif header is None or row is None:
        sys.exit(1)
    # otherwise, simply write what was returned by Param-Medic to stdout
    else:
        print "----------"
        print header
        print row

if __name__ == "__main__":
    main()
