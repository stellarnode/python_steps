#!/usr/bin/env python
# coding: utf-8

# Before running the script, make sure you:
# 1. Provided a file with a list of users
# 2. Provided correct credintials for login - DEV or PROD
# 3. Created a file where the report will be written
# 4. Specified roles that need to be assigned to users
# 5. Specified the codes for the courses users should be enrolled to

from time import sleep
import traceback
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sbn
from datetime import datetime
import requests
import json
from pandas.io.json import json_normalize
import openpyxl as xl
from password_generator import PasswordGenerator

import alemira_batch_create_users_creds as creds

# Choose environment
login = creds.LOGIN_DEV
urls = creds.URLS_DEV
list_of_users_file = creds.LIST_OF_USERS_FILE
account_creation_report_file = creds.ACCOUNT_CREATION_REPORT_FILE
default_password = creds.DEFAULT_PASSWORD

# Configure user settings and enrollments
with_password = True
with_default_password = True
with_enrollment = True
courses_to_enroll = ['2+3+']
# courses_to_enroll = ['ACC-ACP-NH', 'ACC-CPHON', 'ACC-CNSM-APP', 'ACC-APP']

# Configure URLs
auth_URL = urls['auth_URL']
token_URL = urls['token_URL']
base_URL = urls['base_URL']

# Configure password generator
pwo = PasswordGenerator()
pwo.minlen = 10 # (Optional)

try:
    users_to_create = pd.read_excel(list_of_users_file)
    print('[INFO] Imported list of users...')
    print(users_to_create)
    # users_to_create_list = users_to_create.values.tolist()
    users_to_create_dict = users_to_create.to_dict('records')
    print('[INFO] Converted excel to list of objects...')
    print(users_to_create_dict)
except Exception:
    print('Excel file with list of users not found or import completed with error.')
    traceback.print_exc()

response = requests.post(token_URL, data = login, verify = False)
json_response = response.json()
print('[INFO] Authentication...', response.status_code, response.reason)
print(json_response)

if response.status_code > 299 and login == creds.LOGIN_PROD:
    token = creds.TOKEN
    print('[INFO] Authenticating with login credentials.')
else:
    token = json_response['access_token']
    print('[INFO] Authenticating with token.')

headers = {'Authorization': 'Bearer ' + token}

try:
    users = requests.get(base_URL + '/api/v1/users', headers = headers)
    print('[INFO] Getting users to test connection... ', users.status_code, users.reason)
    print('[INFO] Users received...')
    print(users.json())
    print('---')
except:
    print('[WARN] Failed to get users...')
    traceback.print_exc()

# objective_workflows = requests.get(base_URL + '/api/v1/objective-workflow-aggregates', headers = headers)
# print(objective_workflows.status_code, objective_workflows.reason)
# print(objective_workflows.json())

roles = requests.get(base_URL + '/api/v1/roles', headers = headers)

roles_ids = {
    'Learner': '',
    'Author': '',
    'Instructor': '',
    'Admin': ''}

print('[INFO] Getting roles... ', roles.status_code, roles.reason)
print(roles.json())

try:
    for role in roles.json():
        if role['name'] == 'Learner':
            roles_ids['Learner'] = role['id']
            print('Learner: ' + role['id'])
        if role['name'] == 'Author':
            roles_ids['Author'] = role['id']
            print('Author: ' + role['id'])
        if role['name'] == 'Instructor':
            roles_ids['Instructor'] = role['id']
            print('Instructor: ' + role['id'])
        if role['name'] == 'Administrator':
            roles_ids['Admin'] = role['id']
            print('Admin: ' + role['id'])
    print('[INFO] Extracted role ids... ')
    print(roles_ids)
    print('---')
except Exception:
    print('Roles not found or completed with error.')
    print('---')
    traceback.print_exc()

def create_password(user):   
    if not user.get('email'):
        return default_password
    else:
        part = user.get('email').split('@')[0]
        password = part + default_password
        return password

def find_user_if_exists(user, users):
    for x in users:
        if user['email'] == x['email']:
            user['id'] = x['id']
            return user
    return user

def create_user(user):
    new_user = {
        'firstName': user['first_name'],
        'lastName': user['last_name'],
        'email': user['email'],
        'username': user['email'],
        'details': {'city': user['city'], 'school': user['school']}
    }
    
    if with_password and with_default_password:
        new_user['password'] = create_password(user)
    elif with_password:
        new_user['password'] = pwo.generate()
    else:
        pass

    try:
        created_user = requests.post(base_URL + '/api/v1/lms-users', headers = headers, json = new_user)
        print('[INFO] Submitted new user: ' + new_user['firstName'] + ' ' + new_user['lastName'] + ' with ' + new_user['email'])
        print(created_user.status_code, created_user.reason)
        print(created_user.json())
        user['submit_id'] = created_user.json()['id']
        user['check_url'] = created_user.json()['url']
        user['submit_status'] = created_user.status_code

        if with_password:
            user['password'] = new_user['password']
        
        print(user)
        print('---')
    except:
        user['submit_status'] = created_user.status_code
        print('[ERROR] Submitting user for creation has not completed or completed with errors...')
        traceback.print_exc()
    return user

def check_created_user(user):
    if user.get('submit_status') > 299:
        print('[WARN] Skipping check for submitted user...')
        return user
    else:
        try:
            check = requests.get(base_URL + user['check_url'], headers = headers)
            user['id'] = check.json()['entityId']
            user['completed_status'] = check.json()['completed']
            # user['user_url'] = check.json()['completed']['url']
            # user['check_message'] = check.json()['completed']['message']
            print('[INFO] User creation completed...', check.status_code, check.reason)
            print(check.json())
            print('---')
        except:
            print('[ERROR] Could not check user creation...')
            traceback.print_exc()
    return user

def assign_roles(user):
    if not user.get('id') or not user.get('completed_status'):
        print('[WARN] Skipping assigning roles due to possible errors with user creation...')
        return user
    else:
        user['submitted_roles'] = []
        user['role_submitted_statuses'] = []
        user['role_submit_ids'] = []
        user['role_check_urls'] = []
        # Assign Learner role
        learner_role = {
            'userId': user['id'],
            'roleId': roles_ids['Learner'],
            'roleName': 'Learner'
        }

        #Assign Author role
        author_role = {
            'userId': user['id'],
            'roleId': roles_ids['Author'],
            'roleName': 'Author'
        }

        #Assign Instructor role
        instructor_role = {
            'userId': user['id'],
            'roleId': roles_ids['Instructor'],
            'roleName': 'Instructor'
        }

        #Assign Admin role
        admin_role = {
            'userId': user['id'],
            'roleId': roles_ids['Admin'],
            'roleName': 'Administrator'
        }

        # roles_to_assign = [learner_role, author_role, instructor_role, admin_role]
        roles_to_assign = [learner_role]


        for role in roles_to_assign:
            try:
                added_role = requests.post(base_URL + '/api/v1/user-roles', headers = headers, json = role)
                user['role_submitted_statuses'].append(added_role.status_code)
                user['role_submit_ids'].append(added_role.json()['id'])
                user['role_check_urls'].append(added_role.json()['url'])
                user['submitted_roles'].append(role['roleName'])
                print('[INFO] Submitted role ' + role['roleName'] + ' for user ' + user['first_name'] + ' ' + user['last_name'] + ' with ' + user['email'])
                print(added_role.json())
                print('---')
            except:
                print('[ERROR] Errors setting roles...')
                traceback.print_exc()
    return user

def check_assigned_roles(user):
    if not user.get('role_check_urls'):
        print('[WARN] Skipping roles check due to missing URLs...')
        return user
    else:
        # user['roles'] = []
        user['role_ids'] = []
        # user['role_urls'] = []
        user['role_check_messages'] = []

        for url in user['role_check_urls']:
            try:
                check = requests.get(base_URL + url, headers = headers)
                user['role_ids'].append(check.json()['entityId'])
                # user['role_urls'].append(check.json()['completed']['url']) 
                # user['role_check_messages'].append(check.json()['completed']['message'])
                user['role_check_messages'].append(check.json()['completed'])
                print('[INFO] User role checked...')
                print(check.json())
                print('---')
            except:
                print('[ERROR] Could not check roles for user ' + user['first_name'] + ' ' + user['last_name'] + ' with ' + user['email'])
                traceback.print_exc()
        return user

def get_objectives_ids(list_of_codes):
    objectives_ids = []

    try:
        objectives = requests.get(base_URL + '/api/v1/objectives', headers = headers)
        print('[INFO] Getting objectives...', objectives.status_code, objectives.reason)
        print(objectives.json())
        print('---')

        for objective in objectives.json():
            # print(objective)
            if objective['code'] in list_of_codes:
                objectives_ids.append({'code': objective['code'], 'id': objective['id']})
        
        return objectives_ids

    except:
        print('[WARN] Could not retrieve objectives...', objectives.status_code, objectives.reason)
        traceback.print_exc()


def enroll_user_to_objectives(user, objectives):
    personal_enrollments = []

    if not user.get('id'):
        return user

    for objective in objectives:
        personal_enrollment = {
            'objectiveId': objective['id'],
            'userId': user['id'],
            'retake': True
            }    
        try:
            personal_enrollment = requests.post(base_URL + '/api/v1/personal-enrollments', headers = headers, json = personal_enrollment)
            print('[INFO] Creating enrollment for user {} and course {}...'.format(user['first_name'] + ' ' + user['last_name'], objective['code']), personal_enrollment.status_code, personal_enrollment.reason)
            print(personal_enrollment.json())
            print('---')
            personal_enrollments.append(personal_enrollment.json())

        except:
            print('[WARN] Could not create personal enrollment...', personal_enrollment.status_code, personal_enrollment.reason)
            traceback.print_exc()

        sleep(3)

    user['personal_enrollments'] = personal_enrollments
    return user

def check_enrollments(user):
    if not user.get('personal_enrollments'):
        return user
    else:
        user['enrollment_checks'] = []

        for enrollment in user['personal_enrollments']:
            print('[INFO] Checking enrollment...')
            print(enrollment)
            try:
                check = requests.get(base_URL + enrollment['url'], headers = headers)
                user['enrollment_checks'].append(check.json())
                print('[INFO] Completed check for enrollment...')
                print(check.json())
                print('---')
            except:
                print('[ERROR] Could not check enrollment for user ' + user['first_name'] + ' ' + user['last_name'] + ' with ' + user['email'])
                traceback.print_exc()

        return user


for user in users_to_create_dict:
    try:
        user = find_user_if_exists(user, users.json())
        print('[INFO] Existing user...')
        print(user)

        if not user.get('id'):
            user = create_user(user)
            print('Please wait...')
            sleep(5)
            user = check_created_user(user)
        else:
            user['completed_status'] = 'existing user found'

        if not user.get('id') or not user.get('completed_status'):
            print('[WARN] Skipping assigning roles due to possible errors with user creation...')
            print('[INFO] ...or user might already exist.')
        elif user.get('id') or user.get('completed_status'):
            user = assign_roles(user)
            print('Please wait...')
            sleep(5)
            user = check_assigned_roles(user)

    except Exception:
        print('[ERROR] Errors occurred with user: ' + user['first_name'] + ' ' + user['last_name'] + ' with ' + user['email'])
        traceback.print_exc()

if with_enrollment:
    print('---')
    print('[INFO] Users to enroll to courses...')
    print(users_to_create_dict)
    print('---')

    objectives_ids_list = get_objectives_ids(courses_to_enroll)
    print('[INFO] Objectives for enrollments...')
    print(objectives_ids_list)
    print('---')

    for user in users_to_create_dict:
        user = enroll_user_to_objectives(user, objectives_ids_list)
        print('[INFO] Sumbitted personal enrollments...')
        print(user['personal_enrollments'])
        print('---')

    for user in users_to_create_dict:
        user = check_enrollments(user)

report = pd.DataFrame.from_records(users_to_create_dict)

print('[INFO] Done with the following result...')
print(report)

report.to_excel(account_creation_report_file)




