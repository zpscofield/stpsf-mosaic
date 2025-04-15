import os
import csv
import json
from astropy.io import fits

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

i2d_fits_path = config["img_path"] # Mosaic image
csv_filepath = 'exposure_wcs_info.csv' # output wcs CSV file
output_asn_path = 'association.json' # output association file with order matching resampling.

# Read HDRTAB and header for image information
with fits.open(i2d_fits_path) as hdul:
    header = hdul[0].header
    program = header.get("PROGRAM", "program_ID")
    target = header.get("TARGNAME", "target_ID")
    instrument = header.get("INSTRUME", "nircam").lower()
    filter_name = header.get("FILTER")
    pupil = header.get("PUPIL", "clear")
    subarray = header.get("SUBARRAY", "full").lower()
    exp_type = header.get("EXP_TYPE", "nrc_image").lower()

    hdrtab = hdul["HDRTAB"].data
    colnames = hdul["HDRTAB"].columns.names

    # Necessary columns from the HDRTAB
    selected_cols = ['FILENAME', 'EFFEXPTM', 'ROLL_REF', 'FILTER', 'DATE-OBS',
                    'DETECTOR', 'CRVAL1', 'CRVAL2', 'CRPIX1', 'CRPIX2',
                    'CD1_1', 'CD1_2', 'CD2_1', 'CD2_2',
                    'CTYPE1', 'CTYPE2', 'CUNIT1', 'CUNIT2',
                    'WCSAXES', 'RADESYS', 'RA_V1', 'DEC_V1', 'PA_V3',
                    'S_REGION', 'V2_REF', 'V3_REF', 'VPARITY', 'V3I_YANG',
                    'RA_REF', 'DEC_REF', 'ROLL_REF', 'VELOSYS']

    # Ensure that all columns are available
    available_cols = [col for col in selected_cols if col in colnames]

    # write out CSV
    with open(csv_filepath, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=available_cols)
        writer.writeheader()
        for row in hdrtab:
            row_dict = {col: row[col] for col in available_cols}
            writer.writerow(row_dict)

print(f"WCS metadata saved to {csv_filepath}")

# Create association file
expnames = [row['FILENAME'] for row in hdrtab]

members = []
for expname in expnames:
    members.append({
        "expname": expname,
        "exptype": "science",
        "exposerr": None,
        "asn_candidate": "(custom, observation)"
    })

association = {
    "asn_type": "image3",
    "asn_rule": "candidate_Asn_Lv3Image",
    "version_id": None,
    "code_version": "1.9.6",
    "degraded_status": "No known degraded exposures in association.",
    "program": program,
    "constraints": f"DMSAttrConstraint('{{'name': 'program', 'sources': ['program'], 'value': '{program[1:]}'}})\n"
                   f"DMSAttrConstraint('{{'name': 'instrument', 'sources': ['instrume'], 'value': '{instrument}'}})\n"
                   f"DMSAttrConstraint('{{'name': 'opt_elem', 'sources': ['filter'], 'value': '{filter_name}'}})\n"
                   f"DMSAttrConstraint('{{'name': 'opt_elem2', 'sources': ['pupil'], 'value': '{pupil}'}})\n"
                   f"DMSAttrConstraint('{{'name': 'subarray', 'sources': ['subarray'], 'value': '{subarray}'}})\n"
                   f"Constraint_Image('{{'name': 'exp_type', 'sources': ['exp_type'], 'value': '{exp_type}'}})",
    "asn_id": f"{filter_name}_asn",
    "target": target,
    "asn_pool": f"{filter_name}_pool",
    "products": [
        {
            "name": f"{target}_nircam_clear-{filter_name}",
            "members": members
        }
    ]
}

with open(output_asn_path, 'w') as f:
    json.dump(association, f, indent=2)

print(f"Association file created: {output_asn_path}")
