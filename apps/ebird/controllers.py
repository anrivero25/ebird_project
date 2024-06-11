"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_email, get_heatmap_data, prime_checklist_data
from py4web.utils.form import Form, FormStyleBulma
from py4web.utils.grid import Grid, GridClassStyleBulma
from py4web.utils.grid import Column

import urllib.parse #for parsing location url
import json  #added for debugging
import math #for lat and lng calculations
from pydal.validators import IS_NOT_EMPTY #added for location query

url_signer = URLSigner(session)

@action('index')
@action.uses('index.html', db, auth, url_signer)
def index():
    return dict(
        # COMPLETE: return here any signed URLs you need.
        my_callback_url = URL('my_callback', signer=url_signer),
        get_heatmap_data_url = URL('get_heatmap_data', signer=url_signer),  # Add this line
        checklist_url = URL('checklist', signer=url_signer),
        stats_url = URL('stats', signer=url_signer),
        location_url = URL('location', signer=url_signer)
    )

@action('my_callback')
@action.uses() # Add here things like db, auth, etc.
def my_callback():
    # The return value should be a dictionary that will be sent as JSON.
    return dict(my_value=3)

# -------------------------- INDEX PAGE FUNCTIONS -------------------------- #

@action('get_heatmap_data')
@action.uses(db, auth)
def get_heatmap_data_action():
    try:
        species = request.params.get('species', 'all')
        if species is None:
            species = 'all'
        logger.info(f"Received species: {species}")  # Log for debugging
        heatmap_data = get_heatmap_data(species)
        return dict(heatmap_data=heatmap_data)
    except Exception as e:
        logger.error(f"Error in get_heatmap_data_action: {str(e)}")  # Log for debugging
        response.status = 500
        return dict(error=str(e))
    

# -------------------------- CHECKLIST and MY_CHECKLIST PAGE FUNCTIONS -------------------------- #
@action('checklist', method=['POST', 'GET'])
@action.uses('checklist.html', session, db, auth.user, url_signer)
def checklist(): 
    return dict(
            checklist_url = URL('checklist', signer=url_signer),
            my_checklist_url = URL('my_checklist', signer=url_signer),
            edit_checklist_url = URL('edit_checklist', signer=url_signer),
            load_checklists_url = URL('load_checklists'),
            search_species_url = URL('search'),
            inc_count_url = URL('inc_count')
            )

@action('edit_checklist', method=['POST', 'GET'])
@action.uses('edit_checklist.html', db, session, auth.user, url_signer)
def edit_checklist():
    return dict(
            my_checklist_url = URL('my_checklist', signer=url_signer),
            checklist_url = URL('checklist', signer=url_signer),
            load_user_checklists_url = URL('load_user_checklists'),
            edit_checklist_url = URL('edit_checklist', signer=url_signer),
            update_checklist_url = URL('update_checklist'),
            )

@action('my_checklist', method=['POST', 'GET'])
@action.uses('my_checklist.html', session, db, auth.user, url_signer)
def my_checklist(): 
    return dict(
            my_checklist_url = URL('my_checklist', signer=url_signer),
            checklist_url = URL('checklist', signer=url_signer),
            edit_checklist_url = URL('edit_checklist', signer=url_signer),
            load_checklists_url = URL('load_checklists'),
            load_user_checklists_url = URL('load_user_checklists'),
            delete_checklist_url = URL('delete_checklist'),
            search_my_species_url = URL('my_search'),
            )   

@action('load_user_checklists')
@action.uses(db, session, auth.user)
def load_user_checklists():
    user_checklists = db(db.sightings.user_email == get_user_email()).select().as_list()
    return dict(data=user_checklists)
                
@action('load_checklists')
@action.uses(db, session, auth.user)
def load_checklists(): 
    checklist_table_data = db(db.checklist_data).select().as_list()
    return dict(data=checklist_table_data)

@action('inc_count', method='POST') 
@action.uses(db, session, auth.user)
def inc_count(): 
    # Get the count and id from the request
    count = request.json.get('count')
    id = request.json.get('id')
    specie=request.json.get('specie')
    
    # Update data for checklist table
    db.checklists.insert(observer_id=get_user_email(), user_email=get_user_email())
    
    # Add observation to sightings table
    db.sightings.insert(specie=specie, count=count, user_email=get_user_email())

    # Update data for checklist table displayed on server side
    specie = db(db.checklist_data.id == id).select().first()
    specie.total_count += count; 
    specie.update_record()
    return dict(total=specie.total_count)

@action('search')
@action.uses(db, session, auth.user)
def search(): 
    q = request.params.get('q')
    results = db(db.checklist_data.specie.like(f"%{q}%")).select(db.checklist_data.specie,
                                db.checklist_data.total_count, 
                                groupby=db.checklist_data.specie).as_list()
    return dict(results=results)

@action('my_search')
@action.uses(db, session, auth.user)
def my_search(): 
    q = request.params.get('q')
    results = db((db.sightings.specie.like(f"%{q}%")) & (db.sightings.user_email == get_user_email())).select(db.sightings.specie,
                                db.sightings.count).as_list()
    print("rseults", results)
    return dict(results=results)

@action('update_checklist', method='POST')
@action.uses(db, session, auth.user)
def update_checklist(): 

    return dict()

@action('delete_checklist', method='POST')
@action.uses(db, session, auth.user)
def delete_checklist():
    id = request.json.get('id')
    specie = request.json.get('specie')
    count = int(request.json.get('count'))

    # Delete data row from "sightings" table
    db(db.sightings.user_email == get_user_email() and db.sightings.id == id).delete()
    data = db(db.sightings.user_email == get_user_email()).select().as_list()

    # Update total count in "checklist_data" table
    bird = db(db.checklist_data.specie == specie).select().first()
    new_count = bird.total_count - count
    bird.total_count = new_count
    bird.update_record()

    return dict(user_checklists=data)

# -------------------------- LOCATION PAGE FUNCTIONS -------------------------- #
# Define lat and lng as global variables
lat = None
lng = None

@action('location')
@action.uses('location.html', session, db, auth.user, url_signer)
def location():
    global lat, lng 
    # Get latitude and longitude from the request parameters
    signature_param = request.params.get('_signature')
    lat_param = None
    lng_param = request.params.get('lng')

    if signature_param:
        # Decode the signature_param
        try:
            decoded_signature = urllib.parse.unquote(signature_param)
            lat_index = decoded_signature.find('lat=') + len('lat=')
            lat_end_index = decoded_signature.find('&', lat_index)
            lat_param = decoded_signature[lat_index:lat_end_index]
        except Exception as e:
            print(f"Error decoding signature parameter: {e}")

    print('lat_param:', lat_param)
    print('lng_param:', lng_param)
    
    # Convert latitude and longitude from strings to float values if needed
    lat = float(lat_param) if lat_param is not None else None
    lng = float(lng_param) if lng_param is not None else None
    
    print('lat:', lat)
    print('lng:', lng)
    
    # Now you can use lat and lng variables in your page logic
    return dict(latitude=lat, longitude=lng)


@action('api/get_sightings', method=['GET', 'POST'])
@action.uses(db)
def get_sightings():
    global lat, lng  # Access the global variables

    # Ensure latitude and longitude are set
    if lat is None or lng is None:
        return dict(error="Latitude and longitude are not set.")

    # Define the range for latitude and longitude
    lat_range = 10 / 69.0  # Approximately 10 miles in latitude (1 degree of latitude is about 69 miles)
    lng_range = 10 / (69.0 * math.cos(math.radians(lat)))  # Approximately 10 miles in longitude

    # Calculate the latitude and longitude boundaries
    min_lat = lat - lat_range
    max_lat = lat + lat_range
    min_lng = lng - lng_range
    max_lng = lng + lng_range

    print(f"Latitude range: {min_lat} to {max_lat}")
    print(f"Longitude range: {min_lng} to {max_lng}")

    # Fetch sightings within the defined range
    sightings_query = db(
        (db.checklists.latitude.cast('float') >= min_lat) &
        (db.checklists.latitude.cast('float') <= max_lat) &
        (db.checklists.longitude.cast('float') >= min_lng) &
        (db.checklists.longitude.cast('float') <= max_lng)
    ).select(
        db.sightings.ALL,
        db.checklists.ALL,
        join=db.sightings.on(db.sightings.sei == db.checklists.sei),
        orderby=db.checklists.date
    )

    sightings = []
    for sighting in sightings_query:
        sighting_data = {
            'specie': sighting.sightings.specie,
            'count': sighting.sightings.count,
            'date': sighting.checklists.date,
            'latitude': sighting.checklists.latitude,
            'longitude': sighting.checklists.longitude,
            'sei': sighting.checklists.sei,
            'observer_id': sighting.checklists.observer_id,
            'time': sighting.checklists.time
        }
        sightings.append(sighting_data)

    #print(f"Found sightingsss: {sightings}")
    return dict(sightings=sightings)


@action('api/get_species_list', method=['GET', 'POST'])
@action.uses(db)
def get_species_list():
    try:
        global lat, lng  # Access the global variables

        # Ensure latitude and longitude are set
        if lat is None or lng is None:
            return dict(error="Latitude and longitude are not set.")

        # Define the range for latitude and longitude
        lat_range = 10 / 69.0  # Approximately 10 miles in latitude (1 degree of latitude is about 69 miles)
        lng_range = 10 / (69.0 * math.cos(math.radians(lat)))  # Approximately 10 miles in longitude

        # Calculate the latitude and longitude boundaries
        min_lat = lat - lat_range
        max_lat = lat + lat_range
        min_lng = lng - lng_range
        max_lng = lng + lng_range

        # Fetch sightings within the defined range
        sightings_query = db(
            (db.checklists.latitude.cast('float') >= min_lat) &
            (db.checklists.latitude.cast('float') <= max_lat) &
            (db.checklists.longitude.cast('float') >= min_lng) &
            (db.checklists.longitude.cast('float') <= max_lng)
        ).select(
            db.sightings.ALL,
            db.checklists.ALL,
            join=db.sightings.on(db.sightings.sei == db.checklists.sei),
        )

        # Convert the query results to a list of dictionaries
        species_list = sightings_query.as_list()

        # Create a dictionary to count the number of sightings for each species
        sightings_count = {}
        for sighting in species_list:
            # Extract specie field. Adjust field access according to actual structure.
            specie = sighting.get('sightings', {}).get('specie')
            if specie:
                if specie in sightings_count:
                    sightings_count[specie] += 1
                else:
                    sightings_count[specie] = 1

        # Create the final list with species and their sightings count
        final_species_list = []
        for specie, count in sightings_count.items():
            final_species_list.append({'specie': specie, 'sightings': count})

        return dict(speciesList=final_species_list)
    except Exception as e:
        logger.error(f"Error fetching species list: {str(e)}")
        return dict(error=str(e))

@action('api/get_top_contributors', method=['GET', 'POST'])
@action.uses(db)
def get_top_contributors():
    try:
        # Query to count the number of checklists per observer
        query = """
            SELECT observer_id, COUNT(*) as sighting_count
            FROM checklists
            GROUP BY observer_id
            ORDER BY sighting_count DESC
            LIMIT 10;  -- Limit to top 10 contributors
        """
        top_contributors = db.executesql(query, as_dict=True)

        return dict(topContributors=top_contributors)
    except Exception as e:
        logger.error(f"Error fetching top contributors: {str(e)}")
        return dict(error=str(e))
    
# -------------------------- STATISTICS PAGE FUNCTIONS -------------------------- #

@action('stats', method=['POST', 'GET'])
@action.uses('stats.html', session, db, auth.user, url_signer)
def stats(): 
    return dict(
        stats_url = URL('stats', signer=url_signer),
        load_stats_url = URL('load_stats'),
        search_species_url = URL('search'),
        checking_favorite_url = URL('checking_favorite'),
        # dateData_url = URL('dateData'),
        # findingDates_url = URL('findingDates'),
        )

@action('load_stats')
@action.uses(db, session, auth.user)
def load_stats(): 
    user_checklists = db(db.sightings.user_email == get_user_email()).select().as_list()

    # print(db(db.sightings.user_email == get_user_email()).select(db.sightings.count))
    counts = db(db.sightings.user_email == get_user_email()).select(db.sightings.count)

    return dict(data=user_checklists, count=counts)

@action('checking_favorite', method='POST')
@action.uses(db, session, auth.user)
# marking an item as purchased;
def checking_favorite():
    id = request.json.get('id')
    my_db = db(db.sightings.user_email == get_user_email()).select().first()
    assert my_db.user_email == get_user_email() # Only the owner of the observation can inc it. 
    if (my_db.favorite == False):
        my_db.favorite = True
    else:
        my_db.favorite = False
    my_db.update_record()
    return dict(favorite=my_db.favorite)

# @action('findingDates', method='POST')
# @action.uses(db, session, auth.user)
# def findingDates():
#     id = request.json.get('id')
#     print(id)
#     my_db = db(db.sightings.user_email == get_user_email()).select().first()
#     assert my_db.user_email == get_user_email() # Only the owner of the observation can inc it. 
#     if (my_db.favorite == False):
#         my_db.favorite = True
#     else:
#         my_db.favorite = False
#     my_db.update_record()
#     return dict(favorite=my_db.favorite)

# @action('api/get_date_data', method=['GET', 'POST'])
# @action.uses(db)
# def get_date_data():
#     id = request.json.get('id')
#     print(id)
#     my_db = db(db.sightings.user_email == get_user_email()).select().first()
#     counts = db(db.sightings.user_email == get_user_email()).select(db.sightings.count)
#     return dict(favorite=my_db.favorite)