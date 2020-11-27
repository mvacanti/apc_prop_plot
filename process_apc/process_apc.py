import re
import pandas
import matplotlib.pyplot as plt
import os
from argparse import ArgumentParser
import export_jsbsim_xml as ejx


def parse_prop_titles(title_file):
    prop_info = {}
    with open(title_file, 'rt') as title_data:
        for line in title_data:
            file_name = re.search('PER3_.*\.dat', line)
            if file_name:
                end_file_name = file_name.span()[1]
                file_name = file_name[0]
                prop_specs = re.search('\d[\.\d]*x\d[\.\d]*', line[end_file_name:])
                if prop_specs:
                    diameter = float(re.split('x', prop_specs[0])[0])
                    pitch = float(re.split('x', prop_specs[0])[1])
                    prop_descriptors = ''.join(re.findall('\S', re.split('\d[\.\d]*x\d[\.\d]*',line[end_file_name:])[1]))
                    prop_info[file_name] = {'spec_name': prop_specs[0], 'diameter': diameter, 'pitch': pitch,
                                          'descriptors': prop_descriptors, 'full_spec_name': prop_specs[0]
                                          + prop_descriptors}
    title_data.close()
    return prop_info


def select_text_parse(option, text):

    def parse_rpm_data():
        rpm = re.search('\d\d\d*', text)[0]
        return float(rpm)

    def parse_prop_data():
        prop_data = re.findall('[ -]\d*\.\d\d*', text)
        numeric_propdata = []
        for number in prop_data[:8]:
            numeric_propdata.append(float(number))
        return numeric_propdata

    dict = {
        2: parse_rpm_data,
        3: parse_prop_data}

    return dict.get(option)()


def export_prop_data(prop_data_list, rpm_list, prop_name, save_dir):
    df = pandas.DataFrame(prop_data_list,
                          columns=['Diameter', 'Pitch', 'descriptor', 'RPM', 'V', 'J', 'Pe', 'Ct', 'Cp', 'PWR',
                                   'Torque', 'Thrust'])

    reports_dir = os.path.join(save_dir, 'reports')
    prop_report_dir = os.path.join(save_dir, 'reports', prop_name)
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    if not os.path.exists(prop_report_dir):
        os.makedirs(prop_report_dir)

    df.to_csv(os.path.join(prop_report_dir, prop_name + '_J-VAR' + '.csv'))

    plot_var = ['V', 'Pe', 'Ct', 'Cp', 'PWR', 'Torque', 'Thrust']
    y_labels = {'V': 'V (mph)', 'Pe': 'Pe', 'Ct': 'Ct', 'Cp': 'Cp', 'PWR': 'PWR (Hp)',
                'Torque': 'Torque (In-Lbf)', 'Thrust': 'Thrust (Lbf)'}

    rpm_var = pandas.DataFrame(rpm_list, columns=['RPM'])
    for var in plot_var:
        if var not in ['V', 'Pe']:
            try:
                rpm_var[var] = df.loc[df['V'] == 0][var].values
                plt.figure(figsize=(11, 8.5))
                plt.plot(rpm_list, df.loc[df['V'] == 0][var])
                plt.xlabel("RPM")
                plt.ylabel(y_labels[var])
                plt.title("APC " + prop_name)
                plt.savefig(os.path.join(prop_report_dir, prop_name + '_' + '_STATIC-RPM-' + var + '.png'))
                plt.close()
            except ValueError:
                print('Data input format error, see: ' + prop_name)

    rpm_var.to_csv(os.path.join(prop_report_dir, prop_name + '_STATIC-RPM-VAR' + '.csv'))

    for var in plot_var:
        plt.figure(figsize=(11, 8.5))
        for rpm in rpm_list:
            ct = ejx.format_prop_df(df.loc[df['RPM'] == rpm]['J'], df.loc[df['RPM'] == rpm]['Ct'])
            cp = ejx.format_prop_df(df.loc[df['RPM'] == rpm]['J'], df.loc[df['RPM'] == rpm]['Cp'])
            jsb_xml_text = ejx.export_jsb_xml(prop_name, '0.001', str(df.loc[0][0]), '2', str(df.loc[0][1]), ct, cp)

            with open(os.path.join(prop_report_dir, 'APC_' + prop_name + '_' + str(int(rpm)) + '.xml'), 'wt') as jsb_prop_xml:
                jsb_prop_xml.write(jsb_xml_text)
            jsb_prop_xml.close()

            plt.plot(df.loc[df['RPM'] == rpm]['J'], df.loc[df['RPM'] == rpm][var], label=str(rpm))
            plt.legend(title='RPM')
            plt.xlabel("J (Adv Ratio)")
            plt.ylabel(y_labels[var])
            plt.title("APC " + prop_name)
        plt.savefig(os.path.join(prop_report_dir, prop_name + '_J-' + var + '.png'))
        plt.close()


def extract_prop_data(apc_file, prop_title_data):
    prop_base_file = os.path.basename(apc_file)
    try:
        prop_diameter = prop_title_data[prop_base_file]['diameter']
        prop_pitch = prop_title_data[prop_base_file]['pitch']
        prop_descriptors = prop_title_data[prop_base_file]['descriptors']
        prop_name = prop_title_data[prop_base_file]['full_spec_name']

        with open(apc_file, 'rt') as din:
            prop_data = []
            rpm_opt = []
            for line in din:
                search_return = []
                regex_search = {'PROP RPM = *\d\d\d*': 1, '[ -]\d*\.\d\d*': 8}

                for term in regex_search:
                    eval_line = re.findall(term, line)
                    if len(eval_line) >= regex_search[term]:
                        search_return.append(1)
                    else:
                        search_return.append(0)

                if sum(search_return) > 1:
                    print('WARNING: MALFORMED LINE / SEARCH MATCH :' + line + str(search_return))

                if search_return[0] == 1:
                    option = 2
                    rpm = select_text_parse(option, line)
                    rpm_opt.append(rpm)

                elif search_return[1] == 1:
                    option = 3
                    prop_data.append(select_text_parse(option, line))
                    prop_data[-1].insert(0, prop_diameter)
                    prop_data[-1].insert(1, prop_pitch)
                    prop_data[-1].insert(2, prop_descriptors)
                    prop_data[-1].insert(3, rpm)
        din.close()
        return prop_data, rpm_opt, prop_name

    except KeyError:
        print('Unable to find matching prop specification and title data, check prop and title file: ' + prop_base_file)
        input('Press any key to exit...')
        exit()


def batch_process_dir(dir_path, prop_title_data):
    apc_files = os.listdir(dir_path)
    for prop in apc_files:
        if prop.endswith('.dat'):
            print("Processing " + prop)
            working_file = os.path.join(dir_path, prop)
            prop_dat = extract_prop_data(working_file, prop_title_data)
            export_prop_data(prop_dat[0], prop_dat[1], prop_dat[2], dir_path)


if __name__ == "__main__":
    parser = ArgumentParser(description='Process APC Prop Data files')
    parser.add_argument('--dir', help='Directory path for batch APC .dat files.')
    parser.add_argument('--specs', help='File path for APC TITLEDAT.DAT file')
    args = parser.parse_args()

    specs = parse_prop_titles(args.specs)
    batch_process_dir(args.dir, specs)
