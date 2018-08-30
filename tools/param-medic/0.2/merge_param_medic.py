import sys
import os
import re
import numpy

param_medic_result_dirname = sys.argv[1]
percent_files_mod_detected = float(sys.argv[2])
parameters_fname = sys.argv[3]
annotation_fname = sys.argv[4]
out_fname = sys.argv[5]
out_display_fname = sys.argv[6]
out_per_group_summary_fname = sys.argv[7]


def main():
    mangled_to_orig_fname = get_file_mapping(parameters_fname)
    groupname_per_file = read_in_annotation_file(
        annotation_fname, mangled_to_orig_fname
    )

    param_medic_values_d = {}
    for fname in os.listdir(param_medic_result_dirname):
        with open(os.path.join(param_medic_result_dirname, fname)) as f:
            param_medic_header = f.readline().strip().split('\t')
            values = f.readline().strip().split('\t')
            for i, x in enumerate(param_medic_header):
                if x not in param_medic_values_d:
                    param_medic_values_d[x] = []
                param_medic_values_d[x].append(values[i])

    if 'filename' in param_medic_values_d:
        param_medic_values_d['filename'] = [
            mangled_to_orig_fname[z] for z in
            param_medic_values_d['filename'] if
            (z in mangled_to_orig_fname)
        ]
    # overall summary
    out_values, out_display_values = get_summary(
        param_medic_values_d, param_medic_header, percent_files_mod_detected
    )
    with open(out_fname, 'w') as out_f:
        out_f.write('\t'.join(param_medic_header) + '\n')
        out_f.write('\t'.join(out_values) + '\n')
    with open(out_display_fname, 'w') as out_f:
        if param_medic_header and param_medic_header != ['']:
            out_f.write('\t'.join(param_medic_header) + '\n')
            out_f.write('\t'.join(out_display_values) + '\n')
        else:
            out_f.write('status\nParam-Medic not run.\n')

    # per-group summary
    out_display_values_per_group = {}
    all_groups = sorted(set(groupname_per_file.values()))
    for groupname in all_groups:
        group_indices = []  # find indices in param_medic_values_d that apply to this group
        for annot_fname in groupname_per_file:
            if groupname_per_file[annot_fname] != groupname:
                continue
            for i, param_medic_fname in enumerate(param_medic_values_d['filename']):
                if filenames_match(param_medic_fname, os.path.basename(annot_fname)):
                    group_indices.append(i)
        pergroup_param_medic_values_d = {}
        for k in param_medic_values_d:
            v = param_medic_values_d[k]
            pergroup_param_medic_values_d[k] = [
                z for (y, z) in enumerate(v) if y in group_indices
            ]
        out_values, out_display_values = get_summary(
            pergroup_param_medic_values_d, param_medic_header, percent_files_mod_detected
        )
        out_display_values_per_group[groupname] = out_display_values

    with open(out_per_group_summary_fname, 'w') as out_f:
        if param_medic_header and param_medic_header != ['']:
            out_f.write('Group (Condition.BioReplicate.Experiment)\t%s\n' % '\t'.join(param_medic_header))
            for g in all_groups:
                out_f.write('%s\t%s\n' % (g, '\t'.join(out_display_values_per_group[g])))
        else:
            out_f.write('status\nParam-Medic not run.\n')


def filenames_match(fname1, fname2):
    fname1_no_ext = fname1
    if '.' in fname1:
        fname1_no_ext = fname1[:fname1.rindex('.')]
    fname2_no_ext = fname2
    if '.' in fname2:
        fname2_no_ext = fname2[:fname2.rindex('.')]

    return (
        fname1 == fname2 or
        fname1 == fname2_no_ext or
        fname1_no_ext == fname2 or
        fname1_no_ext == fname2_no_ext
    )
        

def get_file_mapping(parameters_fname):
    mangled_to_orig_fname = {}
    with open(parameters_fname) as f:
        for line in f:
            if 'upload_file_mapping' in line:
                mangled_filename = line[line.index('>') + 1:line.index('|')]
                orig_filename = os.path.basename(
                    line[line.rindex('|') + 1:line.rindex('<')]
                )
                mangled_to_orig_fname[mangled_filename] = orig_filename
    return mangled_to_orig_fname


def read_in_annotation_file(annotation_fname, mangled_to_orig_fname):
    groupname_per_file = {}
    annotation_cols = ['Run', 'Condition', 'BioReplicate', 'Experiment']
    with open(annotation_fname) as f:
        f_lines = [z.strip() for z in re.split('[\n\r]', f.read()) if z.strip()]
        if len(f_lines) < 1:
            raise_exception('Invalid annotation file')
        header = f_lines[0]
        if ',' not in header:
            raise_exception('Annotation file does not appear to be a CSV file.')
        header = header.split(',')
        for c in annotation_cols:
            if c not in header:
                raise_exception('Annotation file is missing column "%s"' % c)

        for line in f_lines[1:]:
            line = line.split(',')
            annot_file_fname = line[header.index('Run')]
            groupname = re.sub(
                '\\s', '_', '%s.%s.%s' % (
                    line[header.index('Condition')],
                    line[header.index('BioReplicate')],
                    line[header.index('Experiment')]
                )
            )
            if (
                annot_file_fname in groupname_per_file and
                groupname_per_file[annot_file_fname] != groupname
            ):
                raise_exception(
                    'Filename %s appears multiple times in Run column of '
                    'annotation file' % annot_file_fname
                )
            groupname_per_file[annot_file_fname] = groupname
    return groupname_per_file


def get_summary(
    param_medic_values_d, param_medic_header, percent_files_mod_detected
):
    out_values = []
    out_display_values = []
    for x in param_medic_header:
        values = param_medic_values_d[x]
        if x.endswith('_present'):
            percent_det = divide(values.count('T'), len(values)) * 100.0
            out_str = 'T' if percent_det >= percent_files_mod_detected else 'F'
            out_values.append(out_str)
            out_display_values.append(
                '%s (Present in %d/%d files (%.2f%%))' % (
                    out_str, values.count('T'), len(values), percent_det
                )
            )
        else:
            try:
                proc_values = [float(z) for z in values if z != 'ERROR']
                median = numpy.median(proc_values)
                stdev = numpy.std(proc_values)
                out_values.append(str(median + 2 * stdev))
                out_display_values.append(
                    '%f (Median: %f, SD: %f, %d/%d files (%.2f%%))' % (
                        median + 2 * stdev, median, stdev,
                        len(proc_values), len(values),
                        divide(len(proc_values), len(values)) * 100.0
                    )
                )
            except ValueError:
                if all([z == values[0] for z in values]):
                    out_str = values[0]
                elif len(set(values)) == 2:
                    values_set = list(set(values))
                    count_first_val = values.count(values_set[0])
                    count_second_val = values.count(values_set[1])
                    if count_second_val > count_first_val:
                        values_set = values_set[::-1]
                        temp = count_second_val
                        count_second_val = count_first_val
                        count_first_val = temp
                    out_str = '%s (%d/%d files, %.2f%%), %s (%d/%d files, %.2f%%)' % (
                        values_set[0], count_first_val, len(values),
                        divide(count_first_val, len(values)) * 100.0,
                        values_set[1], count_second_val, len(values),
                        divide(count_second_val, len(values)) * 100.0
                    )
                else:
                    out_str = '; '.join(values)
                if len(out_str) > 5000:
                    out_str = '%s [truncated]' % out_str[:5000]
                out_values.append(out_str)
                out_display_values.append(out_str)
    return (out_values, out_display_values)


def divide(a, b):
    if b != 0:
        return float(a) / b
    else:
        return 0.0


def raise_exception(error_message):
    raise ValueError(
        'Error occurred when summarizing Param-Medic results:\n%s' % error_message
    )

if __name__ == '__main__':
    sys.exit(main()) 



