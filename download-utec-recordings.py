import requests
import shlex
import subprocess
import logging
import os
from datetime import datetime

def check_zoomdl_is_installed():
    # TODO: Check that zoomdl binary is installed
    pass

def set_global_variables():
    """
    Store the values at the .env environment variable in global
    variables.
    """
    global cookies_file, email, x_auth_token, authorization_bearer

    from dotenv import dotenv_values

    config = dotenv_values('.env')

    # Student-dependent variables

    cookies_file = config.get('cookies_file')
    email = config.get('email')
    x_auth_token = config.get('x_auth_token')
    authorization_bearer = config.get('authorization_bearer')

def check_global_variables():
    """
    Check that the global variables are correct.
    """

    # Check that the variables are not None

    # TODO: This is repetitive and can be simplified. This could be
    # simplified if it were possible to obtain the name of a variable

    if not cookies_file:
        raise Exception('The variable cookies_file is None and it must have a value')
    if not email:
        raise Exception('The variable email is None and it must have a value')
    if not x_auth_token:
        raise Exception('The variable x_auth_token is empty and it must have a value')
    if not authorization_bearer:
        raise Exception('The variable authorization_bearer is empty and it must have a value')

    # Checks for cookies_file

    ## Check it exists

    if not os.path.isfile(cookies_file):
        raise Exception('The path stored at cookies_file is not a file')

    ## Check it is readable

    if not os.access(cookies_file, os.R_OK):
        raise Exception('The file stored at cookies_file is not readable')

    ## TODO: Check that it is well formatted. The first line need to
    ## be "# Netscape HTTP Cookie File"

def date_to_scholar_week_in_2021_1(date: str) -> int:
    """
    Given a date, return the scholar week corresponding to that week
    in the semester 2021-1.
    """
    d = datetime.strptime(date, "%Y-%m-%d")
    w = d.strftime('%U')
    w = int(w) - 15
    return w

def get_lectures_metadata():
    """
    Get the metadata of all the lectures.
    """
    first_week_first_day = '2021-04-09'
    last_week_last_day = '2021-08-07'

    headers = {
        'X-Auth-Token': x_auth_token,
        'Authorization': 'Bearer ' + authorization_bearer
    }

    data = {
        'codPrograma': 1,
        'codPeriodo': 402,
        'email': email,
        'fechaInicio': first_week_first_day,
        'fechaFin': last_week_last_day
    }

    r = requests.post('https://api.utec.edu.pe/conference-api/v1/conference/list/meeting/student',
                      headers = headers,
                      json = data)

    response = r.json()

    # TODO: Throw an exception when the request failed.

    lectures = response.get('content')

    return lectures

def remove_lectures_not_able_to_download(lectures):
    """
    Remove recordings that can't be downloaded

    A recording can't be downloaded when it is null or it is a Google
    Drive link.
    """
    import re

    recording_regex = re.compile(r'http(s)?://utec\.zoom\.us/rec/play/')
    able_to_download = []

    for lecture in lectures:

        recording_url = lecture.get('playUrl')

        # If the lecture didn't have a recording URL, then don't add it.

        if not recording_url:
            continue

        # If the lecture is not a Zoom link, then don't add it.

        if not recording_regex.match(recording_url):
            continue

        able_to_download.append(lecture)

    return able_to_download

def get_lectures_filename_and_url(lectures):
    """
    Get the filename and the download URL for each lecture.
    """
    lectures_filename_and_url = []

    for lecture in lectures:
        item = {}

        # Get the data

        lecture_url_recording = lecture.get('playUrl')
        conference = lecture.get('conference')
        course_id = conference.get('idCourse') if conference else None
        course_name = conference.get('nameCourse') if conference else None
        lecture_type = conference.get('descriptionTypeSesion') if conference else None
        lecture_date = lecture.get('startTime')
        lecture_date_scholar_week = date_to_scholar_week_in_2021_1(lecture_date)

        # Modify the data

        lecture_date_scholar_week = '%02d' % lecture_date_scholar_week

        # Collect the data

        filename = f"""{course_id} ^ {course_name} ^ {lecture_date_scholar_week} ^ {lecture_date} ^ {lecture_type}"""

        item['filename'] = filename
        item['url'] = lecture_url_recording

        lectures_filename_and_url.append(item)

    return lectures_filename_and_url

def download_lecture(recording_url, filename):
    """
    Download the recording stored at recording_url and store it in
    filename.
    """

    # TODO: Does zomdl always use mp4?

    zoomdl_extension = 'mp4'

    if os.path.isfile(filename + '.' + zoomdl_extension):
        logging.info('Not downloading recording with filename {filename}, because it already exists.')
        return

    # TODO: Use the zoomdl module for more flexibility

    filename = shlex.quote(filename)
    recording_url = shlex.quote(recording_url)
    cmd = f"""zoomdl --cookies {cookies_file} -f {filename} -u {recording_url}"""

    print(cmd)
    subprocess.run(cmd, shell=True)

set_global_variables()
check_global_variables()
lectures = get_lectures_metadata()
lectures = remove_lectures_not_able_to_download(lectures)
lectures = get_lectures_filename_and_url(lectures)

for lecture in lectures:
    download_lecture(lecture['url'],
                     lecture['filename'])
