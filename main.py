import streamlit as st
import pandas as pd
import requests
import random
import math
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from st_social_media_links import SocialMediaIcons
from shapely.geometry import Point, Polygon
from st_keyup import st_keyup


st.set_page_config(page_title='Vacayzen | Quick Order Form', page_icon=':material/shopping_bag:')


hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            .block-container
            {
                padding-top: 1rem;
                margin-top: 1rem;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


if 'STATE' not in st.session_state:
    st.session_state.STATE = 'GREETING'

if 'CUSTOMER' not in st.session_state:
    st.session_state.CUSTOMER = {
    'arrival':        None,
    'departure':      None,
    'stay_address':   None,
    'stay_latitude':  None,
    'stay_longitude': None,
    'stay_area':      None,
    'stay_forbid':    None,
    'name':           None,
    'phone_number':   None,
    'email_address':  None,
    'how':            None,
    }




def Header(withLinks):
    l, m, r = st.columns(3)
    m.image(st.secrets['logo'])

    if withLinks:
        st.markdown('**WAYS TO ORDER**')
        st.button('⚡️ **ORDER ONLINE BELOW** (SAVE 5%) ⚡️', use_container_width=True)
        l, r = st.columns(2)
        l.link_button('BY E-MAIL', st.secrets['email'], use_container_width=True)
        r.link_button('BY PHONE',  st.secrets['phone'], use_container_width=True)





def Greeting():
    st.title('Place Order')


def Goodbye():
    st.write('')
    st.success('**Order request submitted!**')
    st.info('An agent will be in touch shortly.')
    st.write('')
    socials = SocialMediaIcons(st.secrets['socials'])
    socials.render()





def Address_to_Coordinates(address):

    url      = st.secrets['geo_url']
    params   = {'singleLine': address, 'f': 'json', 'maxLocations': 1 }
    response = requests.get(url, params=params)

    if response.status_code == 200:

        data = response.json()

        if 'candidates' in data and data['candidates']:
            address  = data['candidates'][0]['address']
            location = data['candidates'][0]['location']

            return {
                'address':   address,
                'coordinates': [location['y'], location['x']]
                }
    
    return None


def Check_Against_Geofences(latitude, longitude):
    geofences = pd.read_json('geofences.json')
    point     = Point(longitude, latitude)

    for geofence in geofences:
        geofence_area = geofences[geofence]['area']
        polygon       = Polygon(geofence_area)

        if polygon.contains(point):
            return {'name': geofence, 'forbid': geofences[geofence]['forbid']}
        
    return {'name': None,     'forbid': None}

def Get_Place_Suggestions(input_text):
    endpoint = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
    params = {
        'input': input_text,
        'location': st.secrets['map_location'],
        'radius': st.secrets['map_radius'],
        'components': 'country:us',
        'language': 'en',
        'types': "address",
        'key': st.secrets['map_key']
    }
    response = requests.get(endpoint, params=params)
    return response.json()

def Get_Customer_Stay():

    if "suggestions" not in st.session_state:
        st.session_state.suggestions = []

    l, r      = st.columns(2)

    st.session_state.CUSTOMER['arrival']   = l.date_input('When do you arrive?', min_value=pd.to_datetime('today'))
    st.session_state.CUSTOMER['departure'] = r.date_input('When do you depart?', value=st.session_state.CUSTOMER['arrival']+pd.Timedelta(days=1), min_value=st.session_state.CUSTOMER['arrival']+pd.Timedelta(days=1))

    st.session_state.CUSTOMER['arrival']   = st.session_state.CUSTOMER['arrival'].strftime('%m/%d/%Y')
    st.session_state.CUSTOMER['departure'] = st.session_state.CUSTOMER['departure'].strftime('%m/%d/%Y')

    l, r      = st.columns([1,2])

    with l:
        address = st_keyup('Where will you be staying?', placeholder='Start typing here...', debounce=200)

    if address:
        suggestions = Get_Place_Suggestions(address)
        if suggestions.get("predictions"):
            predictions = [prediction["description"] for prediction in suggestions["predictions"]]
            st.session_state.suggestions = predictions
            
        else:
            st.session_state.suggestions = []

    st.session_state.CUSTOMER['stay_address'] = r.selectbox("Full address:", st.session_state.suggestions)


    if st.button('Begin Shopping', use_container_width=True, type='primary'):
        if not st.session_state.CUSTOMER['stay_address']:
            st.warning('Please provide an address.')

        else:
            location = Address_to_Coordinates(st.session_state.CUSTOMER['stay_address'])

            if not location['coordinates']:
                st.warning('Invalid address. Please enter a valid address.')

            else:
                st.session_state.CUSTOMER['stay_address']   = location['address']
                st.session_state.CUSTOMER['stay_latitude']  = location['coordinates'][0]
                st.session_state.CUSTOMER['stay_longitude'] = location['coordinates'][1]

                area = Check_Against_Geofences(st.session_state.CUSTOMER['stay_latitude'], st.session_state.CUSTOMER['stay_longitude'])

                if not area:
                    st.warning('The address provided is incomplete or incorrect. Please double-check your entry.')

                else:
                    st.session_state.CUSTOMER['stay_area']   = area['name']
                    st.session_state.CUSTOMER['stay_forbid'] = area['forbid']

                    st.session_state.STATE = 'SHOP'
                    Shop()



def Get_Guest_Details():
    st.header('About You')

    if 'famous_name' not in st.session_state:
        famous_names = ['Keanu Reeves','Bruce Lee','Albert Einstein','Elivs Presley','Captain America','Clark Kent']
        st.session_state.famous_name  = random.choice(famous_names)

    if 'punny_email' not in st.session_state:
        punny_emails = ['relaxing@thebeach.now','laughing@greatjokes.haha','looking@sunsets.wow']
        st.session_state.punny_email  = random.choice(punny_emails)

    options = [
        'Property Manager',
        'Saw Equipment / Vehicles',
        'Online (Google, Facebook, etc.)',
        'A friend told us about you.',
        'Other.'
        ]

    l, m, r = st.columns(3)

    st.session_state.CUSTOMER['name']          = l.text_input('What is your name?',   placeholder=st.session_state.famous_name)
    st.session_state.CUSTOMER['phone_number']  = m.text_input('Your phone number?',   placeholder='123-456-7890')
    st.session_state.CUSTOMER['email_address'] = r.text_input('Your e-mail address?', placeholder=st.session_state.punny_email)
    how                                        = st.selectbox('How did you hear about Vacayzen?', options=options, placeholder='Choose an option.', index=None)

    if how == 'Other.':
        how_2 = st.text_input('Can you elaborate on how you heard about us?', placeholder='Our meeting was destiny.')
        st.session_state.CUSTOMER['how'] = how_2
    else:
        st.session_state.CUSTOMER['how'] = how




def ItemCard(asset):
    isMinimum = not math.isnan(asset['attributes'].MinimumRate)

    rate = [f'${asset['attributes'].FirstDayRate}', f'${asset['attributes'].AdditionalDayRate}', f'${asset['attributes'].MinimumRate}']

    with st.container(border=True):
        if isMinimum:
            rate = pd.DataFrame([rate], columns=['First','Additional','Minimum'])
            st.write(f'**{asset['name']}**')
        else:
            rate = rate[:2]
            rate = pd.DataFrame([rate], columns=['First','Additional'])
            st.markdown(f'**{asset['name']}**')
        
        st.dataframe(rate, use_container_width=True, hide_index=True)
        count = st.number_input('Quantity',0,step=1, key=f'asset_{asset['name']}', label_visibility='collapsed')





def Shop():
    assets    = {}
    df        = pd.read_json('assets.json')

    if st.session_state.CUSTOMER['stay_forbid'] != [] and st.session_state.CUSTOMER['stay_forbid'] is not None:
        st.info(f'You will be staying in **{st.session_state.CUSTOMER['stay_area']}**, and the community does not permit: **{', '.join(st.session_state.CUSTOMER['stay_forbid'])}**. These products have been removed from the below product offering for your benefit.', icon=':material/wrong_location:')
    else:
        if st.session_state.CUSTOMER['stay_area']:
            st.info(f'You will be staying in **{st.session_state.CUSTOMER['stay_area']}**, and the community permits our whole product offering!', icon=':material/where_to_vote:')
    
    Get_Guest_Details()

    for asset in df:
        if (st.session_state.CUSTOMER['stay_forbid'] is not None) and (df[asset].Product in st.session_state.CUSTOMER['stay_forbid']):
            continue

        if df[asset].Product not in assets:
            assets[df[asset].Product] = []
            assets[df[asset].Product].append({'name': asset, 'attributes': df[asset]})
        else:
            assets[df[asset].Product].append({'name': asset, 'attributes': df[asset]})
    
    for asset_group in assets:
        st.header(f'**{asset_group}**', help=assets[asset_group][0]['attributes'].AssetDescription)

        for asset in assets[asset_group]:
            ItemCard(asset)
    
    st.header('Additional Services', help='An agent will provide more information on services per your request.')
    services = [
        'Beach Bonfires',
        'Airport Transfer / Transport',
        'Private Chef',
        'Grocery Shopping',
        'Sunset Photoshoot',
        'Fishing Trips',
        'Paddleboard & Kayak Rentals',
        'Babysitting'
    ]

    placement = 0
    with st.container(border=True):
        st.write(f'Check if you would like additional information on the following:')
        st.write(f'')
        l, r = st.columns(2)

        for service in services:
            match placement:
                case 0:
                    l.checkbox(service, key=f'check_{service}')
                    placement = 1
                case 1:
                    r.checkbox(service, key=f'check_{service}')
                    placement = 0
    
    
    if st.button('🏖️ Submit', use_container_width=True, type='primary', key='shop_checkout'):
        st.toast('Submitting...')
        interest_array = []
        
        for key in st.session_state.keys():
            if st.session_state[key]:
                interest = ''
                if 'check_' in key:
                    interest = key[6:]
                    interest_array.append(interest)
        
        interests = '\n'.join(interest_array)

        asset_array = []

        for key in st.session_state.keys():
            if 'asset_' in key:
                asset = ''
                if st.session_state[key] > 0:
                    asset = f'({st.session_state[key]}) {key[6:]}'
                    asset_array.append(asset)
        
        assets = '\n'.join(asset_array)

        submission = {
            'submitted_time': pd.to_datetime('today').strftime('%m/%d/%Y %H:%M:%S'),
            'name': st.session_state.CUSTOMER['name'],
            'phone_number': st.session_state.CUSTOMER['phone_number'],
            'email_address': st.session_state.CUSTOMER['email_address'],
            'how': st.session_state.CUSTOMER['how'],
            'start_date': st.session_state.CUSTOMER['arrival'],
            'end_date': st.session_state.CUSTOMER['departure'],
            'area': st.session_state.CUSTOMER['stay_area'],
            'address': st.session_state.CUSTOMER['stay_address'],
            'more_info_requestd': interests,
            'assets': assets,
        }

        credentials  = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets['key'], st.secrets['scope'])
        client       = gspread.authorize(credentials)
        sheet        = client.open(st.secrets['sheet']).worksheet(st.secrets['tab'])  
        row          = list(submission.values())
        sheet.append_row(row)

        st.session_state.STATE = 'DONE'
        st.rerun()


        
    




match st.session_state.STATE:
    case 'GREETING':
        Header(withLinks=True)
        Greeting()
        Get_Customer_Stay()
    case 'SHOP':
        Header(withLinks=True)
        Greeting()
        Get_Customer_Stay()
        Shop()
    case 'DONE':
        Header(withLinks=False)
        Goodbye()