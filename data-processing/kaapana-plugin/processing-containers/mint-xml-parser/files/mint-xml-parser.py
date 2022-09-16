import glob
import os
import xml.etree.ElementTree as et
from os.path import dirname
from pathlib import Path

import pandas as pd


def get_all_cases(root) -> list:
    cases = []
    for trial in root.iter('Trial'):
        for trialArm in trial.iter('TrialArm'):
            for case in trialArm.iter('Case'):
                cases.append(case)
    return cases


def parse_assessment(case):
    import itertools
    return [
        dict(
            case_id=case.attrib['CaseID'],
            case_name=case.attrib['CaseName'],
            patient_id=[*case.iter('Patient')][0].attrib['PatientID'],
            assessment_id=assessment.attrib['AssessmentID'],
            **{
                Question.attrib['Label']: Question.attrib['Answer']
                for Question in assessment.iter('Question')
            },
            dicom_studies=";".join([
                study.attrib['StudyUID']
                for study in assessment.iter('DicomStudy')
            ]),
            dicom_series=";".join(list(itertools.chain(*[
                [
                    series.attrib['SeriesUID']
                    for series in study.iter('DicomSeries')
                ]
                for study in assessment.iter('DicomStudy')
            ])))
        )
        for assessment in case.iter('Assessment')
    ]


def xml2csv(path_to_xml, target_dir):
    out_file = str(Path(path_to_xml.replace(dirname(path_to_xml), target_dir)).with_suffix(".csv"))

    tree = et.parse(path_to_xml)
    root = tree.getroot()
    cases = get_all_cases(root)

    parsed_cases = []
    exceptions = []

    for case in cases:
        try:
            case_lesions = parse_assessment(case)
            parsed_cases.extend(case_lesions)
        except Exception as e:
            exceptions.append(e)

    df = pd.DataFrame.from_records(parsed_cases)
    df.to_csv(out_file)
    print(f'{out_file} written successfully')

# From the template
batch_folders = sorted(
    [f for f in glob.glob(os.path.join('/', os.environ['WORKFLOW_DIR'], os.environ['BATCH_NAME'], '*'))])

for batch_element_dir in batch_folders:

    element_input_dir = os.path.join(batch_element_dir, os.environ['OPERATOR_IN_DIR'])
    element_output_dir = os.path.join(batch_element_dir, os.environ['OPERATOR_OUT_DIR'])
    if not os.path.exists(element_output_dir):
        os.makedirs(element_output_dir)

    # The processing algorithm
    print(f'Checking {element_input_dir} for dcm files and writing results to {element_output_dir}')
    xml_files = sorted(glob.glob(os.path.join(element_input_dir, "*.xml"), recursive=True))

    if len(xml_files) == 0:
        print("No xml file found!")
    else:
        for xml_file in xml_files:
            print(f'Parsing XML-file: {xml_file}')
            xml2csv(xml_file, element_output_dir)
            print(f'Successfully parsed: {xml_file}')

