#Longdiffusion heuristic

# File:     longdiffusion_heuristic.py
# Date:
# Desc:     heuristic file to curate the Concordia project into BIDS format

import os

#################################################################################
####################  Create keys for each acquisition type  ####################
#################################################################################

def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes

#anat
t1w = create_key(
    'sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_T1w')

#dwi
dwi = create_key(
    'sub-{subject}/ses-{session}/dwi/sub-{subject}_ses-{session}_dwi')

#fmap
b0_phase = create_key(
   'sub-{subject}/{session}/fmap/sub-{subject}_{session}_phase{item}')

b0_mag = create_key(
   'sub-{subject}/{session}/fmap/sub-{subject}_{session}_magnitude{item}')

AP_epi = create_key(
   'sub-{subject}/{session}/fmap/sub-{subject}_acq-dMRI_dir-AP_epi')

PA_epi = create_key(
   'sub-{subject}/{session}/fmap/sub-{subject}_acq-dMRI_dir-PA_epi')

topup = create_key(
    'sub-{subject}/{session}/fmap/sub-{subject}_acq-dMRI_topup_epi')
#b0_mag1 = create_key(
#   'sub-{subject}/{session}/fmap/sub-{subject}_{session}_magnitude1')
#b0_mag2 = create_key(
#   'sub-{subject}/{session}/fmap/sub-{subject}_{session}_magnitude2')

#################################################################################
###########  Define rules to map scans to the correct BIDS filename  ############
#################################################################################

#Institution name: PENN - HUP; NEUM - MPI for Human Development; UTMB - UTMB 3T SKYRA

def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where
    allowed template fields - follow python string module:
    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """

    info = {t1w: [],
        dwi: [],
        #gre: [], gre_e1: [], gre_e2: [], gre_e2_ph: [],
        b0_phase: [], b0_mag: [],
        AP_epi: [], PA_epi: [], topup: []
        #rest: [], Ex: [], In: [], ER: [],
        #asl: [], m0: []
    }

    def get_latest_series(key, s):
        info[key].append(s.series_id)

    for s in seqinfo:
        protocol = s.protocol_name.lower()

        if "MPRAGE" in s.series_description:
                get_latest_series(t1w, s)
        elif "T1w" in s.series_description:
            get_latest_series(t1w, s)
        #DWI
        elif "ABCD_dMRI" in s.series_description:
            if "ABCD_dMRI_DistortionMap_PA" not in s.series_description and "ABCD_dMRI_DistortionMap_AP" not in s.series_description:
                get_latest_series(dwi, s)
        elif "dwi" in s.series_description:
            if "AP_epi" in s.series_description:
                get_latest_series(AP_epi, s)
            elif "PA_epi" in s.series_description:
                get_latest_series(PA_epi, s)
            else:
                get_latest_series(dwi, s)
        elif "DTI" in s.series_description:
            if "topup" in s.series_description:
                get_latest_series(topup, s)
            else:
                get_latest_series(dwi, s)
        elif "MULTISHELL" in s.series_description:
            if "b2000" in s.series_description:
                get_latest_series(dwi, s)
            elif "topup" in s.series_description:
                get_latest_series(topup, s)
        elif "TRACEW" in s.series_description:
            get_latest_series(dwi, s)
        #FMAPS
        elif "B0map" in s.series_description:
            #if "Field_map" and "e1" in s.dcm_dir_name:
            #if "e1" in s.dcm_dir_name:
            if s.dcm_dir_name.endswith("e1_ph.nii.gz"):
                get_latest_series(b0_phase, s)
            elif s.dcm_dir_name.endswith("_e1.nii.gz"):
                get_latest_series(b0_mag, s)
            elif s.dcm_dir_name.endswith("e2_ph.nii.gz"):
                get_latest_series(b0_phase, s)
            elif s.dcm_dir_name.endswith("_e2.nii.gz"):
                get_latest_series(b0_mag, s)
            # Looks like there are some dcm_dir_names that end with ph.nii.gz but don't have an e1 or e2 in front of them. Do you want to skip these? 
            else:
                continue
        #elif "fmap" in s.series_description:
        #    if "dir-AP" in s.series_description:
        #        get_latest_series(AP_epi, s)
        #    elif "dir-PA" in s.series_description:
        #        get_latest_series(PA_epi, s)
        elif "dMRIdistmap_dir-AP" in protocol:
            get_latest_series(AP_epi, s)
        elif "dMRIdistmap_dir-PA" in protocol:
            get_latest_series(PA_epi, s)
        #elif "fmap_acq-dMRIdistmap_dir-AP_epi" in protocol:
        #    get_latest_series(AP_epi, s)
        #elif "fmap_acq-dMRIdistmap_dir-PA_epi" in protocol:
        #    get_latest_series(PA_epi, s)
        #elif "fmap-ABCD_acq-dMRIdistmap_dir-PA" in s.series_description:
        #    get_latest_series(PA_epi, s)
        #elif "fmap-ABCD_acq-dMRIdistmap_dir-AP" in s.series_description:
        #    get_latest_series(AP_epi, s)
        elif "dMRI_DistortionMap_AP" in s.series_description:
            get_latest_series(AP_epi, s)
        elif "dMRI_DistortionMap_PA" in s.series_description:
            get_latest_series(PA_epi, s)

    return info

#################################################################################
################     Additional metadata, Fieldmap intention,     ###############
################  Associated sidecards, Rename subject / session  ###############
#################################################################################

################### Hardcode required params in MetadataExtras ##################
##MetadataExtras = {
    # ToDo: If necessary, hardcode missing metadata fields for certain scan types.
    #       (Likely will need to do this if there is ASL data in the project!)

    # example: {
    #    "MetadataField_1": value_1,
    #    "MetadataField_2": value_2,
    #    ...
    #    "MetadataField_N: value_N"
    # }

##}

############ Dictionary mapping fieldmap to scans intended to correct ###########
#IntendedFor = {
    #gre: [

    #    'sub-{subject}/ses-{session}/dwi/sub-{subject}_ses-{session}_dwi',
    #    'sub-{subject}/ses-{session}/func/sub-{subject}_ses-{session}_task-rest_bold',
    #    'sub-{subject}/ses-{session}/func/sub-{subject}_ses-{session}_task-ex_bold',
    #    'sub-{subject}/ses-{session}/func/sub-{subject}_ses-{session}_task-in_bold',
    #    'sub-{subject}/ses-{session}/func/sub-{subject}_ses-{session}_task-er_bold',
    #    'sub-{subject}/ses-{session}/perf/sub-{subject}_ses-{session}_asl',
    #    'sub-{subject}/ses-{session}/perf/sub-{subject}_ses-{session}_m0scan'
    #]
#}

############################### Attach Extra Files ##############################
# e.g. Used for attaching events.tsv files to sessions with fmri task scans
# e.g. Used for attaching aslcontext.tsv file to sessions with asl scans

##def AttachToSession():

##    import pandas as pd

    # ToDo: fill in path to task events.tsv file
##    df = pd.read_csv("<path_to_events_tsv_for_task_1>", sep='\t')

    # Define task 1 events.tsv file
    # ToDo: replace <task_name_1> with actual task name, in variable and in string below.
##    task_name_1_events = {
##        'name': 'sub-{subject}/{session}/func/sub-{subject}_{session}_task-<task_name_1>_events.tsv',
##        'data': df.to_csv(index=False, sep='\t'),
##        'type': 'text/tab-separated-values'
##    }

    # Define task 2 events.tsv file
    # ToDo: replace <task_name_2> with actual task name, in variable and in string below.
##    task_name_2_events = {
##        'name': 'sub-{subject}/{session}/func/sub-{subject}_{session}_task-<task_name_2>_events.tsv',
##        'data': df.to_csv(index=False, sep='\t'),
##        'type': 'text/tab-separated-values'
##    }

    # ToDo: Return list of task_name_events vars you just created.
##    return [task_name_1_events, task_name_2_events]

####################### Rename session and subject labels #######################
# This function queries Flywheel to generate a dictionary (session_labels) that
# maps the existing session label (sess.label) to a new session label in the
# form: <proj_abbreviation><session_index>.

#def gather_session_indices():

    ##import flywheel
    ##fw = flywheel.Client()

    ##proj = fw.projects.find_first('label="{}"'.format("NSCOR_831353"))
    ##subjects = proj.subjects()

    # Initialize session label dictionary where:
    #   Key:    existing session label
    #   Value:  new session label in form <proj_abbreb><session idx>.
    #session_labels = {}

    # Loop through all subjects in Flywheel project
    ##for s in range(len(subjects)):
        # Get a list of the subject's sessions
        ##sessions = subjects[s].sessions()
        ##if sessions:
            # Sort session list by timestamp
            #sessions = sorted(sessions, key=lambda x: x.timestamp)
            # Loop through the subject's sessions, assign each session an index
            ##for i, sess in enumerate(sessions):
            ##    session_labels[sess.label] = "NSCOR" + str(i + 1)

    ##return session_labels

# This line calls the above function.
##session_labels = gather_session_indices()

# Replace session label with <proj_abbrev><session_idx>
##def ReplaceSession(ses_label):
    ##return str(session_labels[ses_label])

#Replace subject label, e.g. Remove leading "0" from session label
##def ReplaceSubject(label):
    ##return label.lstrip("0")
