import streamlit as st
import requests
import base64
import uuid
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CERNER_CLIENT_ID = os.getenv("CERNER_CLIENT_ID")
CERNER_CLIENT_SECRET = os.getenv("CERNER_CLIENT_SECRET")
CERNER_TENANT_ID = os.getenv("CERNER_TENANT_ID")
CERNER_AUTH_SERVER_URL = f"https://authorization.cerner.com/tenants/{CERNER_TENANT_ID}/protocols/oauth2/profiles/smart-v1/personas/provider/authorize"
CERNER_TOKEN_ENDPOINT = f"https://authorization.cerner.com/tenants/{CERNER_TENANT_ID}/protocols/oauth2/profiles/smart-v1/token"
CERNER_REDIRECT_URI = "https://fhir-app-template.streamlit.app"
CERNER_AUDIENCE_URL = f"https://fhir-ehr.cerner.com/r4/{CERNER_TENANT_ID}"

def get_fhir_url():
    params = {
        "response_type": "code",
        "client_id": CERNER_CLIENT_ID,
        "redirect_uri": CERNER_REDIRECT_URI,
        "scope": "user/Practitioner.read user/Patient.read user/Observation.read openid profile",
        "state": str(uuid.uuid4()),
        "aud": CERNER_AUDIENCE_URL
    }
    oauth2_url = requests.Request('GET', CERNER_AUTH_SERVER_URL, params=params).prepare().url
    return oauth2_url

def get_fhir_url_launch(launch):
    params = {
        "response_type": "code",
        "client_id": CERNER_CLIENT_ID,
        "redirect_uri": CERNER_REDIRECT_URI,
        "scope": "user/Practitioner.read user/Patient.read user/Observation.read launch openid profile",
        "state": str(uuid.uuid4()),
        "aud": CERNER_AUDIENCE_URL,
        "launch": launch
    }
    oauth2_url = requests.Request('GET', CERNER_AUTH_SERVER_URL, params=params).prepare().url
    return oauth2_url

def get_fhir_token(auth_code):
    auth_string = f"{CERNER_CLIENT_ID}:{CERNER_CLIENT_SECRET}".encode("ascii")
    base64_bytes = base64.b64encode(auth_string)
    base64_string = base64_bytes.decode("ascii")
    
    auth_headers = {
        "Authorization": f"Basic {base64_string}",
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": CERNER_REDIRECT_URI,
        "client_id": CERNER_CLIENT_ID,
        "client_secret": CERNER_CLIENT_SECRET
    }
    
    response = requests.post(CERNER_TOKEN_ENDPOINT, headers=auth_headers, data=data)
    return response.json()

def standalone_launch(url: str, text: str= None, color="#aa8ccc"):
    st.markdown(
    f"""
    <a href="{url}" target="_self">
        <div style="
            display: inline-block;
            padding: 0.5em 1em;
            color: #FFFFFF;
            background-color: {color};
            border-radius: 3px;
            text-decoration: none;">
            {text}
        </div>
    </a>
    """,
    unsafe_allow_html=True
    )

def get_practitioner(user_profile_url, access_token):
    headers = {
        "Accept": "application/fhir+json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(user_profile_url, headers=headers)
    return response.json()

def get_patient(access_token, person_id):
    base_url = f"https://fhir-ehr.cerner.com/r4/{CERNER_TENANT_ID}/Patient"
    headers = {
        "Accept": "application/fhir+json",
        "Authorization": f"Bearer {access_token}"
    }
    query_params = {
        "_id": person_id
    }
    
    response = requests.get(base_url, headers=headers, params=query_params)
    return response.json()

def get_observation(access_token, person_id):
    base_url = f"https://fhir-ehr.cerner.com/r4/{CERNER_TENANT_ID}/Observation"
    headers = {
        "Accept": "application/fhir+json",
        "Authorization": f"Bearer {access_token}"
    }
    query_params = {
        "patient": person_id
    }
    
    response = requests.get(base_url, headers=headers, params=query_params)
    return response.json()

def fhir_params():
    query_params = st.experimental_get_query_params()
    auth_code = query_params.get("code")
    iss_param = query_params.get("iss")
    launch_param = query_params.get("launch")
    
    return auth_code, iss_param, launch_param

def main():
    logo, title = st.columns([1,1])
    logo_image = 'logo.jpg'

    with logo:
        st.image(logo_image)

    auth_code, iss_param, launch_param = fhir_params()
    
    if auth_code is None and iss_param is None:
        fhir_login_url = get_fhir_url()
        st.subheader("Our App's Launch Capabilities")
        st.markdown("""
        1. EHR Launch: Seamlessly integrates with your EHR system.
        2. Standalone Launch: No need for an EHR to start up. This app can independently access FHIR data as long as it's authorized and provided the relevant iss URL.
        """)
        st.subheader("How It Works")
        st.markdown("""
        * When the app gets a launch request, it seeks permission to access FHIR data.
        * It does this by directing the browser to the EHR's authorization point.
        * Depending on certain rules and potential user approval, the EHR authorization system either approves or denies the request.
        * If approved, an authorization code is sent to the app, which is then swapped for an access token.
        * This access token is your key to the EHR's resource data.
        * Should a refresh token be provided with the access token, the app can utilize it to obtain a fresh access token once the original expires.
        """)
        
        standalone_launch(fhir_login_url, "Login")

    if iss_param is not None:
        fhir_login_url = get_fhir_url_launch(launch_param[0])
        st.write(f"""
        <meta http-equiv="refresh" content="0; URL={fhir_login_url}">
        """, unsafe_allow_html=True)
    
    if auth_code:
        if 'token' in st.session_state and 'access_token' in st.session_state.token:
            token = st.session_state.token
        else:
            token = get_fhir_token(auth_code[0])
            if token.get('error') == 'invalid_grant':
                fhir_login_url = get_fhir_url()
                st.markdown("""
                Session Expired
                """)
                standalone_launch(fhir_login_url, "Login") 
                return
            else:
                st.session_state.token = token

        access_token = token.get('access_token')
        st.session_state.access_token = access_token
        
        header, payload, signature = token.get('id_token').split('.')
        decoded_payload = base64.urlsafe_b64decode(payload + '==').decode('utf-8')
        
        person_id = None

        if 'person_id' not in st.session_state:
            st.session_state.person_id = token.get('patient', "12724065") # If no person_id is provided, app defaults to WILMA SMART

        person_id = st.session_state.person_id

        if 'profile_data' not in st.session_state:
            st.session_state.profile_data = json.loads(decoded_payload)
        if 'practitioner_data' not in st.session_state:
            st.session_state.practitioner_data = get_practitioner(st.session_state.profile_data.get('profile'), access_token)
        if 'patient_data' not in st.session_state:
            patient_data = get_patient(access_token, person_id)
            if 'entry' in patient_data:
                st.session_state.patient_data = patient_data
            else:
                st.session_state.patient_data = None
        if 'observation_data' not in st.session_state:
            observation_data = get_observation(access_token, person_id)
            if 'entry' in observation_data:
                st.session_state.observation_data = observation_data
            else:
                st.session_state.observation_data = None
        
        resource_list = ['Profile', 'Practitioner', 'Patient', 'Observation']
        resource = st.sidebar.selectbox("Resource:", resource_list, index=0)
        
        if resource == 'Profile':
            with title:
                st.markdown('')
                st.subheader('Cerner Profile')
            profile_data = st.session_state.profile_data
            profile_username = profile_data["sub"]
            profile_full_name = profile_data["name"]
            profile_token_iat = profile_data["iat"]
            profile_token_exp = profile_data["exp"]
            profile_token_iat = datetime.utcfromtimestamp(profile_token_iat).strftime('%Y-%m-%d %H:%M:%S UTC')
            profile_token_exp = datetime.utcfromtimestamp(profile_token_exp).strftime('%Y-%m-%d %H:%M:%S UTC')
            st.markdown("*This data shows profile details of the user currently signed in*")
            st.markdown(f"""
            * **Username:** {profile_username}
            * **Name:** {profile_full_name}
            * **Token Issued:** {profile_token_iat}
            * **Token Expiration:** {profile_token_exp}
            """)
            if st.checkbox('Show JSON Response'):
                st.json(st.session_state.profile_data)
        if resource == 'Practitioner':
            with title:
                st.markdown('')
                st.subheader('Practitioner Resource')
            practitioner_data = st.session_state.practitioner_data
            practitioner_name = practitioner_data["name"][0]["text"]
            practitioner_npi = next(identifier["value"] for identifier in practitioner_data["identifier"] if identifier["type"]["coding"][0]["code"] == "NPI")
            practitioner_email = next(telecom["value"] for telecom in practitioner_data["telecom"] if telecom["system"] == "email")
            st.markdown("*This data shows details in the practitioner endpoint of the user currently signed in*")
            st.markdown(f"""
            * **Practitioner Name:** {practitioner_name}
            * **NPI:** {practitioner_npi}
            * **Email:** {practitioner_email}
            """)
            if st.checkbox('Show JSON Response'):
                st.json(st.session_state.practitioner_data)
        if resource == 'Patient':
            with title:
                st.markdown('')
                st.subheader('Patient Resource')
            if st.session_state.patient_data is None:
                st.markdown("No patient data available.")
            else:
                patient_data = st.session_state.patient_data
                patient_name = patient_data['entry'][0]['resource']['name'][0]['text']
                patient_status = patient_data['entry'][0]['resource']['active']
                if patient_status is True:
                    patient_status = 'active'
                else:
                    patient_status = 'inactive'
                patient_phone = next((telecom['value'] for telecom in patient_data['entry'][0]['resource']['telecom'] if telecom['system'] == 'phone'), None)
                patient_address = patient_data['entry'][0]['resource']['address'][0]
                patient_address = f"{patient_address['line'][0]}, {patient_address['city']}, {patient_address['state']} {patient_address['postalCode']}, {patient_address['country']}"
                patient_email = next((telecom['value'] for telecom in patient_data['entry'][0]['resource']['telecom'] if telecom['system'] == 'email'), None)
                patient_dob = patient_data['entry'][0]['resource']['birthDate']
                patient_gender = patient_data['entry'][0]['resource']['gender']
                patient_pref_lang = patient_data['entry'][0]['resource']['communication'][0]['language']['text']
                patient_marital_status = patient_data['entry'][0]['resource']['maritalStatus']['text']
                contact_person = patient_data['entry'][0]['resource']['contact'][0]
                contact_person_name = contact_person['name']['text']
                contact_person_phone = contact_person['telecom'][0]['value']
                contact_person_relationship = contact_person['relationship'][0]['text']
                st.markdown(f"*This data shows details in the patient endpoint of patient ID: {person_id}*")
                st.markdown(f"""
                * **Name:** {patient_name}
                * **Status:** {patient_status}
                * **Phone:** {patient_phone}
                * **Address:** {patient_address}
                * **Email:** {patient_email}
                * **DOB:** {patient_dob}
                * **Gender:** {patient_gender}
                * **Preferred Language:** {patient_pref_lang}
                * **Marital Status:** {patient_marital_status}
                * **Contact Person Name:** {contact_person_name}
                * **Contact Person Phone:** {contact_person_phone}
                * **Contact Person Relationship:** {contact_person_relationship}
                """)
                if st.checkbox('Show JSON Response'):
                    st.json(st.session_state.patient_data)
        if resource == 'Observation':
            with title:
                st.markdown('')
                st.subheader('Observation Resource')
            if st.session_state.observation_data is None:
                st.markdown("No patient data available.")
            else:
                observation_data = st.session_state.observation_data
                weight_with_date = []
                bp_with_date = []
                for i in observation_data.get('entry', []):
                    resource = i.get('resource', {})
                    status = resource.get('status', '')
                    if status == 'final':
                        category_list = resource.get('category', [])
                        for category in category_list:
                            category_coding = category.get('coding', [])
                            for coding in category_coding:
                                if coding.get('code', '') == 'vital-signs':
                                    code_info = resource.get('code', {})
                                    code_coding = code_info.get('coding', [])
                                    for code in code_coding:
                                        display = code.get('display', '')
                                        if display.lower() in ['weight measured']:
                                            value_quantity = resource.get('valueQuantity', {})
                                            value = value_quantity.get('value', 'N/A')
                                            unit = value_quantity.get('unit', '')
                                            effective_date = resource.get('effectiveDateTime', 'N/A')
                                            weight_with_date.append({
                                                'Value': value,
                                                'Unit': unit,
                                                'Date': effective_date
                                            })
                    code_data = resource.get('code', {})
                    if any(coding.get('code', '') == '85354-9' for coding in code_data.get('coding', [])):
                        effective_date_time = resource.get('effectiveDateTime', 'N/A')
                        
                        systolic_pressure = None
                        diastolic_pressure = None
                        
                        for component in resource.get('component', []):
                            code_comp_data = component.get('code', {})
                            
                            # Systolic blood pressure
                            if any(coding.get('code', '') in ['8460-8', '8480-6'] for coding in code_comp_data.get('coding', [])):
                                value_quantity = component.get('valueQuantity', {})
                                systolic_pressure = {
                                    'value': value_quantity.get('value', 'N/A'),
                                    'unit': value_quantity.get('unit', '')
                                }
                                
                            # Diastolic blood pressure
                            if any(coding.get('code', '') in ['8454-1', '8462-4'] for coding in code_comp_data.get('coding', [])):
                                value_quantity = component.get('valueQuantity', {})
                                diastolic_pressure = {
                                    'value': value_quantity.get('value', 'N/A'),
                                    'unit': value_quantity.get('unit', '')
                                }
                                
                        if systolic_pressure and diastolic_pressure:
                            bp_with_date.append({
                                'Date': effective_date_time,
                                'Systolic': systolic_pressure,
                                'Diastolic': diastolic_pressure
                            })
                st.markdown(f"*This data shows details in the observation endpoint of patient ID: {person_id}*")
                if weight_with_date:
                    st.subheader("Weight")
                    for i in weight_with_date:
                        st.markdown(f"""
                        **Date:** {i['Date']}
                        * **Weight:** {i['Value']}{i['Unit']}
                        """)
                if bp_with_date:
                    st.subheader("Blood Pressure")
                    for j in bp_with_date:
                        st.markdown(f"""
                        **Date:** {j['Date']}
                        * **Systolic:** {j['Systolic']['value']}{j['Systolic']['unit']}, **Diastolic:** {j['Diastolic']['value']}{j['Diastolic']['unit']}
                        """)
                if st.checkbox('Show JSON Response'):
                    st.json(st.session_state.observation_data)

if __name__ == "__main__":
    main()
