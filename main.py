import streamlit.components.v1 as components
import streamlit as st
import pandas as pd
import requests
import random
import string
import math
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from st_social_media_links import SocialMediaIcons
from shapely.geometry import Point, Polygon
from st_keyup import st_keyup


st.set_page_config(page_title='Vacayzen Quick Order', page_icon=':material/shopping_bag:')


meta_pixel = """
<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '1368733537438792');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=1368733537438792&ev=PageView&noscript=1"
/></noscript>
<!-- End Meta Pixel Code -->
"""

components.html(meta_pixel, height=1)


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
    'session_id':     None,
    }




def Header(withLinks):
    l, m, r = st.columns(3)
    m.image(st.secrets['logo'])

    if withLinks:
        st.button('⚡️ **ORDER BELOW** (SAVE 5%) ⚡️', use_container_width=True)
        l, r = st.columns(2)
        l.link_button('ORDER BY E-MAIL', st.secrets['email'], use_container_width=True)
        r.link_button('ORDER BY PHONE',  st.secrets['phone'], use_container_width=True)


def Greeting():
    st.title('Place Order')


def Goodbye():
    st.write('')
    st.success('**Order request submitted!**')
    st.info('An agent will be in touch shortly.')
    st.write('')
    socials = SocialMediaIcons(st.secrets['socials'])
    socials.render()


# def Address_to_Coordinates(address):

#     url      = st.secrets['geo_url']
#     params   = {'singleLine': address, 'f': 'json', 'maxLocations': 1 }
#     response = requests.get(url, params=params)

#     if response.status_code == 200:

#         data = response.json()

#         if 'candidates' in data and data['candidates']:
#             address  = data['candidates'][0]['address']
#             location = data['candidates'][0]['location']

#             return {
#                 'address':   address,
#                 'coordinates': [location['y'], location['x']]
#                 }
    
#     return None


# def Check_Against_Geofences(latitude, longitude):
#     geofences = pd.read_json('geofences.json')
#     point     = Point(longitude, latitude)

#     for geofence in geofences:
#         geofence_area = geofences[geofence]['area']
#         polygon       = Polygon(geofence_area)

#         if polygon.contains(point):
#             return {'name': geofence, 'forbid': geofences[geofence]['forbid']}
        
#     return {'name': None,     'forbid': None}


# def Get_Place_Suggestions(input_text):
#     endpoint = 'https://maps.googleapis.com/maps/api/place/autocomplete/json'
#     params = {
#         'input': input_text,
#         'location': st.secrets['map_location'],
#         'radius': st.secrets['map_radius'],
#         'components': 'country:us',
#         'language': 'en',
#         'types': "address",
#         'key': st.secrets['map_key']
#     }
#     response = requests.get(endpoint, params=params)
#     return response.json()

def Get_Guest_Details():
    options = [
        'Text (SMS)',
        'E-mail',
        'Phone',
        ]

    l, m, r = st.columns(3)

    st.session_state.CUSTOMER['name']          = l.text_input('What is your name?',   placeholder='Jane Doe')
    st.session_state.CUSTOMER['phone_number']  = m.text_input('Your phone number?',   placeholder='123-456-7890')
    st.session_state.CUSTOMER['email_address'] = r.text_input('Your e-mail address?', placeholder='email@gmail.com')
    st.session_state.CUSTOMER['how']           = st.selectbox('Preferred method of contact?', options=options, placeholder='Choose an option.', index=0)

def Get_Customer_Stay():

    if "suggestions" not in st.session_state:
        st.session_state.suggestions = []

    l, r      = st.columns(2)

    st.session_state.CUSTOMER['arrival']   = l.date_input('When do you arrive?', min_value=pd.to_datetime('today'))
    st.session_state.CUSTOMER['departure'] = r.date_input('When do you depart?', value=st.session_state.CUSTOMER['arrival']+pd.Timedelta(days=1), min_value=st.session_state.CUSTOMER['arrival']+pd.Timedelta(days=1))

    st.session_state.CUSTOMER['arrival']   = st.session_state.CUSTOMER['arrival'].strftime('%m/%d/%Y')
    st.session_state.CUSTOMER['departure'] = st.session_state.CUSTOMER['departure'].strftime('%m/%d/%Y')

    Get_Guest_Details()

    # l, r      = st.columns([1,2])

    # with l:
    #     address = st_keyup('Where will you be staying?', placeholder='Start typing here...', debounce=200)

    # if address:
    #     suggestions = Get_Place_Suggestions(address)
    #     if suggestions.get("predictions"):
    #         predictions = [prediction["description"] for prediction in suggestions["predictions"]]
    #         st.session_state.suggestions = predictions
            
    #     else:
    #         st.session_state.suggestions = []

    # st.session_state.CUSTOMER['stay_address'] = r.selectbox("Full address:", st.session_state.suggestions)


    # if st.button('Begin Shopping', use_container_width=True, type='primary'):
    #     if not st.session_state.CUSTOMER['stay_address']:
    #         st.warning('Please provide an address.')

    #     else:
    #         location = Address_to_Coordinates(st.session_state.CUSTOMER['stay_address'])

    #         if not location['coordinates']:
    #             st.warning('Invalid address. Please enter a valid address.')

    #         else:
    #             st.session_state.CUSTOMER['stay_address']   = location['address']
    #             st.session_state.CUSTOMER['stay_latitude']  = location['coordinates'][0]
    #             st.session_state.CUSTOMER['stay_longitude'] = location['coordinates'][1]

    #             area = Check_Against_Geofences(st.session_state.CUSTOMER['stay_latitude'], st.session_state.CUSTOMER['stay_longitude'])

    #             if not area:
    #                 st.warning('The address provided is incomplete or incorrect. Please double-check your entry.')

    #             else:
    #                 st.session_state.CUSTOMER['stay_area']   = area['name']
    #                 st.session_state.CUSTOMER['stay_forbid'] = area['forbid']

    #                 st.session_state.STATE = 'SHOP'
    #                 Shop()

    Shop()





def Item_Card(asset):
    # isMinimum = not math.isnan(asset['attributes'].MinimumRate)

    # rate = [f'${asset['attributes'].FirstDayRate}', f'${asset['attributes'].AdditionalDayRate}', f'${asset['attributes'].MinimumRate}']

    # with st.container(border=True):
    #     if isMinimum:
    #         rate = pd.DataFrame([rate], columns=['1st Day','Additional','Minimum'])
    #         st.write(f'**{asset['name']}**')
    #     else:
    #         rate = rate[:2]
    #         rate = pd.DataFrame([rate], columns=['1st Day','Additional'])
    #         st.markdown(f'**{asset['name']}**')
        
    #     st.dataframe(rate, use_container_width=True, hide_index=True)
    #     count = st.number_input('Quantity',0,step=1, key=f'asset_{asset['name']}', label_visibility='collapsed')

    with st.container(border=True):
        st.markdown(f'**{asset['name']}**')
        
        st.write(fr'1st Day: \${asset['attributes'].FirstDayRate}, Additional: \${asset['attributes'].AdditionalDayRate}')
        count = st.number_input('Quantity',0,step=1, key=f'asset_{asset['name']}', label_visibility='collapsed')


def Get_Interests():
    array = []
        
    for key in st.session_state.keys():
        if st.session_state[key]:
            interest = ''
            if 'check_' in key:
                interest = key[6:]
                array.append(interest)
    
    interests = '\n'.join(array)

    return interests


def Get_Assets():
    array = []

    for key in st.session_state.keys():
        if 'asset_' in key:
            asset = ''
            if st.session_state[key] > 0:
                asset = f'({st.session_state[key]}) {key[6:]}'
                array.append(asset)
    
    assets = '\n'.join(array)

    return assets


def Get_Submission(interests, assets):
    submission = {
        'submitted_time':     pd.to_datetime('today').strftime('%m/%d/%Y %H:%M:%S'),
        'session_id':         st.session_state.CUSTOMER['session_id'],
        'name':               st.session_state.CUSTOMER['name'],
        'phone_number':       st.session_state.CUSTOMER['phone_number'],
        'email_address':      st.session_state.CUSTOMER['email_address'],
        'how':                st.session_state.CUSTOMER['how'],
        'start_date':         st.session_state.CUSTOMER['arrival'],
        'end_date':           st.session_state.CUSTOMER['departure'],
        # 'area':               st.session_state.CUSTOMER['stay_area'],
        # 'address':            st.session_state.CUSTOMER['stay_address'],
        'more_info_requestd': interests,
        'assets':             assets,
    }

    return submission


def Get_Session_ID(ids):
    session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))

    while (session_id in ids):
        session_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))

    return session_id


def Is_Valid_Name(name):
    return name != None and name != ''


def Is_Valid_Phone(number):
    return len(number) >= 10


def Is_Valid_Email(email):
    return '@' in email and '.' in email


def Shop():
    assets    = {}
    df        = pd.read_json('assets.json')

    if st.session_state.CUSTOMER['stay_forbid'] != [] and st.session_state.CUSTOMER['stay_forbid'] is not None:
        st.info(f'You will be staying in **{st.session_state.CUSTOMER['stay_area']}**, and the community does not permit: **{', '.join(st.session_state.CUSTOMER['stay_forbid'])}**. These products have been removed from the below product offering for your benefit.', icon=':material/wrong_location:')
    else:
        if st.session_state.CUSTOMER['stay_area']:
            st.info(f'You will be staying in **{st.session_state.CUSTOMER['stay_area']}**, and the community permits our whole product offering!', icon=':material/where_to_vote:')
    
    # Get_Guest_Details()

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

        if asset_group == 'Bike Rentals':
            with st.expander(f'Tap for {asset_group}', expanded=False):
                for asset in assets[asset_group]:
                    Item_Card(asset)
        else:
            for asset in assets[asset_group]:
                Item_Card(asset)
    
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
    
    
    if st.button('SUBMIT', use_container_width=True, type='primary', key='shop_checkout'):
        isValidName  = Is_Valid_Name(st.session_state.CUSTOMER['name'])
        isValidPhone = Is_Valid_Phone(st.session_state.CUSTOMER['phone_number'])
        isValidEmail = Is_Valid_Email(st.session_state.CUSTOMER['email_address'])

        if not isValidName:  st.warning('Please provide a name for your submission.')
        if not isValidPhone: st.warning('Please provide a valid phone number with area code for your submission.')
        if not isValidEmail: st.warning('Please provide a valid e-mail address for your submission.')
        if isValidName and isValidPhone and isValidEmail:

            st.toast('Submitting...')

            credentials  = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets['key'], st.secrets['scope'])
            client       = gspread.authorize(credentials)
            sheet        = client.open(st.secrets['sheet']).worksheet(st.secrets['tab'])

            id_values    = sheet.get_values(st.secrets['id_range'])
            ids          = []
            
            for value in id_values:
                if value[0] != '':
                    ids.append(value[0])
            
            st.session_state.CUSTOMER['session_id'] = Get_Session_ID(ids)

            interests  = Get_Interests()
            assets     = Get_Assets()
            submission = Get_Submission(interests, assets)

            entry      = list(submission.values())
            sheet.append_row(entry)

            st.session_state.STATE = 'DONE'
            st.rerun()


match st.session_state.STATE:
    case 'GREETING':
        Header(withLinks=True)
        Greeting()
        Get_Customer_Stay()
    # case 'SHOP':
    #     Header(withLinks=True)
    #     Greeting()
    #     Get_Customer_Stay()
    #     Shop()
    case 'DONE':
        Header(withLinks=False)
        Goodbye()