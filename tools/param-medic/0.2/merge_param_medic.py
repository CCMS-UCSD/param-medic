import sys
import os
import numpy

param_medic_result_dirname = sys.argv[1]
percent_files_mod_detected = float(sys.argv[2])
out_fname = sys.argv[3]
out_display_fname = sys.argv[4]

def main():
    values_d = {}
    for fname in os.listdir(param_medic_result_dirname):
        with open(os.path.join(param_medic_result_dirname, fname)) as f:
            header = f.readline().strip().split('\t')
            values = f.readline().strip().split('\t')
            for i, x in enumerate(header):
                if x not in values_d:
                    values_d[x] = []
                values_d[x].append(values[i])

    out_values = []
    out_display_values = []
    for x in header:
        values = values_d[x]
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

    with open(out_fname, 'w') as out_f:
        out_f.write('\t'.join(header) + '\n')
        out_f.write('\t'.join(out_values) + '\n')

    with open(out_display_fname, 'w') as out_f:
        if header and header != ['']:
            out_f.write('\t'.join(header) + '\n')
            out_f.write('\t'.join(out_display_values) + '\n')
        else:
            out_f.write('status\nParam-Medic not run.\n')


def divide(a, b):
    if b != 0:
        return float(a) / b
    else:
        return 0.0


if __name__ == '__main__':
    sys.exit(main()) 

