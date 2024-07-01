import streamlit as st
import pandas as pd
import requests
import random
import math
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from st_social_media_links import SocialMediaIcons
from shapely.geometry import Point, Polygon


st.set_page_config(page_title='Vacayzen | Quick Order Form', page_icon=':material/shopping_bag:')

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
    'name_first':     None,
    'name_last':      None,
    'phone_number':   None,
    'email_address':  None,
    'how':            None,
    }




def Header(withLinks):
    l, m, r = st.columns(3)
    m.image(st.secrets['logo'])

    if withLinks:
        st.write('**WAYS TO ORDER**')
        l, r = st.columns(2)
        l.link_button('⚡️ QUICK ORDER FORM ⚡️', "#quick-order-form", use_container_width=True, help='10% OFF',)
        l.link_button('WEBSITE', 'https://www.vacayzen.com', use_container_width=True, help='10% OFF')
        r.link_button('BY E-MAIL', st.secrets['email'], use_container_width=True, help='5% OFF')
        r.link_button('BY PHONE', st.secrets['phone'], use_container_width=True)





def Greeting(withDiscount):
    st.title('Quick Order', help="Browse **Vacayzen**'s top products in a shop that is **catered to your stay**.")
    
    if withDiscount:
        st.success('Orders placed here will have a **10% discount** applied automatically.')


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

        if "candidates" in data and data["candidates"]:
            address  = data["candidates"][0]["address"]
            location = data["candidates"][0]["location"]

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


def Get_Customer_Stay():
    st.markdown('**ABOUT YOUR STAY**', help='We use this information **to save you time and clicks** during your booking process.')

    l, r      = st.columns(2)

    st.session_state.CUSTOMER['arrival']   = l.date_input('When is your arrival?', min_value=pd.to_datetime('today'))
    st.session_state.CUSTOMER['departure'] = r.date_input('When do you depart?', value=st.session_state.CUSTOMER['arrival']+pd.Timedelta(days=1), min_value=st.session_state.CUSTOMER['arrival']+pd.Timedelta(days=1))

    st.session_state.CUSTOMER['arrival']   = st.session_state.CUSTOMER['arrival'].strftime('%m/%d/%Y')
    st.session_state.CUSTOMER['departure'] = st.session_state.CUSTOMER['departure'].strftime('%m/%d/%Y')

    st.session_state.CUSTOMER['stay_address'] = st.text_input('What is the complete address for where you will you be staying?', placeholder='123 Four Street, Destin, FL 32540')

    if st.button('Begin Shopping', use_container_width=True, type='primary'):
        if not st.session_state.CUSTOMER['stay_address']:
            st.warning('Please provide an address to proceed.')

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

                    # st.session_state.STATE = 'SHOP'
                    # st.rerun()
                    Shop()



def Get_Guest_Details():
    st.header('About You')

    if 'famous_name' not in st.session_state:
        famous_names = ['Keanu Reeves','Bruce Lee','Albert Einstein','Elivs Presley','Captain America','Clark Kent']
        st.session_state.famous_name = random.choice(famous_names).split()

    if 'punny_email' not in st.session_state:
        punny_emails = ['relaxing@thebeach.now','laughing@greatjokes.haha','looking@sunsets.wow']
        st.session_state.punny_email  = random.choice(punny_emails)

    options = [
        'Our property manager told us about you.',
        'We saw your equipment (trucks, bikes, golf carts, etc).',
        'We found you online (Google, Facebook, etc).',
        'A friend told us about you.',
        'Other.'
        ]

    l, m, r = st.columns(3)

    st.session_state.CUSTOMER['name_first']    = l.text_input('What is your first name?', placeholder=st.session_state.famous_name[0])
    st.session_state.CUSTOMER['name_last']     = m.text_input('Your last name?',          placeholder=st.session_state.famous_name[1])
    st.session_state.CUSTOMER['email_address'] = r.text_input('Your e-mail address?',     placeholder=st.session_state.punny_email)

    l, r = st.columns([1,2])
    st.session_state.CUSTOMER['phone_number']  = l.text_input('Your phone number?',     placeholder='123-456-7890')
    how                                        = r.selectbox('How did you hear about Vacayzen?', options=options, placeholder='Choose an option.', index=None)

    if how == 'Other.':
        how_2 = st.text_input('Can you elaborate on how you heard about us?', placeholder='Our meeting was destiny.')
        st.session_state.CUSTOMER['how'] = how_2
    else:
        st.session_state.CUSTOMER['how'] = how



def ItemCard(asset):
    isMinimum = not math.isnan(asset['attributes'].MinimumRate)

    with st.container(border=True):
        l, r = st.columns(2)
        if isMinimum:
            l.markdown(f'**{asset['name']}**', help=f'First Day Rate: ${asset['attributes'].FirstDayRate}\n\nAdditional Day Rate: ${asset['attributes'].AdditionalDayRate}\n\nMinimum Rate: ${asset['attributes'].MinimumRate}')
        else:
            l.markdown(f'**{asset['name']}**', help=f'First Day Rate: ${asset['attributes'].FirstDayRate}\n\nAdditional Day Rate: ${asset['attributes'].AdditionalDayRate}')
        count = r.number_input('Quantity',0,step=1, key=f'asset_{asset['name']}', label_visibility='collapsed')





def Shop():
    assets    = {}
    df        = pd.read_json('assets.json')

    if st.session_state.CUSTOMER['stay_forbid'] != [] and st.session_state.CUSTOMER['stay_forbid'] is not None:
        st.info(f'You will be staying in **{st.session_state.CUSTOMER['stay_area']}**, and the community does not permit: **{', '.join(st.session_state.CUSTOMER['stay_forbid'])}**. These products have been removed from the below product offering for your benefit.', icon=':material/wrong_location:')
    else:
        if st.session_state.CUSTOMER['stay_area']:
            st.info(f'You will be staying in **{st.session_state.CUSTOMER['stay_area']}**, and the community permits our whole product offering!', icon=':material/where_to_vote:')
    

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
    
    st.header(f'**Additional Services**', help='Check the boxes for additional services that you would like to learn more about.')
    services = [
        'Beach Bonfires',
        'Sunset Photoshoot',
        'Airport Transfer / Transport',
        'Private Chef',
        'Grocery Shopping',
        'Fishing Trips',
        'Paddleboard & Kayak Rentals',
        'Babysitting'
    ]

    placement = 0
    with st.container(border=True):
        l, r = st.columns(2)

        for service in services:
            match placement:
                case 0:
                    l.checkbox(service, key=f'check_{service}')
                    placement = 1
                case 1:
                    r.checkbox(service, key=f'check_{service}')
                    placement = 0
    
    Get_Guest_Details()
    
    if st.button('🏖️ Submit', use_container_width=True, type='primary', key='shop_checkout'):
        interest_array = []
        
        for key in st.session_state.keys():
            if st.session_state[key]:
                interest = ''
                if 'check_' in key:
                    interest = key[6:]
                    interest_array.append(interest)
        
        interests = ', '.join(interest_array)

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
            'first_name': st.session_state.CUSTOMER['name_first'],
            'last_name': st.session_state.CUSTOMER['name_last'],
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
        Greeting(withDiscount=True)
        Get_Customer_Stay()
    case 'SHOP':
        Header(withLinks=True)
        Greeting(withDiscount=True)
        Shop()
    case 'DONE':
        Header(withLinks=False)
        Goodbye()
