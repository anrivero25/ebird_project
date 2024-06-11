"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth
from pydal.validators import *
import csv # To read csv files

import pandas as pd

def get_heatmap_data(species_name='all'):
    # Load CSV files
    checklists_df = pd.read_csv('./csvfiles/checklists.csv')
    sightings_df = pd.read_csv('./csvfiles/sightings.csv')
    # print(checklists_df)
    
    # Join sightings with checklists on SAMPLING EVENT IDENTIFIER
    sightings_with_location_df = pd.merge(sightings_df, checklists_df, on='SAMPLING EVENT IDENTIFIER')

    if species_name != 'all':
        sightings_with_location_df = sightings_with_location_df[sightings_with_location_df['COMMON NAME'] == species_name]
    
    # Remove non-numeric values in OBSERVATION COUNT
    sightings_with_location_df = sightings_with_location_df[pd.to_numeric(sightings_with_location_df['OBSERVATION COUNT'], errors='coerce').notnull()]
    
    # Prepare data for heatmap: [latitude, longitude, intensity]
    heatmap_data = sightings_with_location_df[['LATITUDE', 'LONGITUDE', 'OBSERVATION COUNT']].copy()
    heatmap_data['OBSERVATION COUNT'] = heatmap_data['OBSERVATION COUNT'].astype(float)
    
    return heatmap_data.values.tolist()

def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None

def get_user_id():
    return auth.current_user.get('id') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow()

# -------------------------- ADDED FUNCTIONS -------------------------- #
# Should we start with row 1 instead of row 0 in these functions ??
# - Because the first line shows what information is contained in each line

# Function to prime the species database
# species.csv contains the species of birds (about 400)
def prime_species():
    if db(db.species).isempty():
        with open('./csvfiles/species.csv', 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            for row in reader:
                db.species.insert(specie=row[0])

# Function to prime the checklists database
# checklists.csv contains the checklists
def prime_checklists():
    if db(db.checklists).isempty():
        with open('./csvfiles/checklists.csv', 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            for row in reader:
                db.checklists.insert(
                    sei=row[0],
                    latitude=row[1],
                    longitude=row[2],
                    date=row[3],
                    time=row[4],
                    observer_id=row[5],
                    duation=row[6],
                    user_id=None,
                    user_email=None  
                )

# Function to prime the sightings database
# sightings.csv contains the sightings
# Each sighting has a checklist, a species, and a number of birds seen.
def prime_sightings():
    if db(db.sightings).isempty():
        with open('./csvfiles/sightings.csv', 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            for row in reader:
                db.sightings.insert(
                    sei=row[0],
                    specie=row[1],
                    count=row[2],
                    favorite=False,  # Default value
                    user_email=None
                )

# Prime the checklist_data database s
# Aggregates data from sightings database, grouping by species and getting the total count per specie
def prime_checklist_data():
    data = db(db.sightings).select(db.sightings.specie, db.sightings.count.sum().with_alias('total_count'), 
                                groupby=db.sightings.specie).as_list()
    for row in data:
        db.checklist_data.update_or_insert((db.checklist_data.specie == row['sightings']['specie']),
                                           specie=row['sightings']['specie'], total_count=row['total_count'])

# -------------------------- DATABASES -------------------------- #

### SPECIES DATABASE ###
# COMMON NAME
db.define_table('species',
    Field('specie')        # SPECIE - common name of the specie
)
prime_species()

### CHECKLIST DATABASE ###
# SAMPLING EVENT IDENTIFIER,LATITUDE,LONGITUDE,OBSERVATION DATE,TIME OBSERVATIONS STARTED,OBSERVER ID,DURATION MINUTES
db.define_table('checklists',
    Field('sei'),           # SAMPLING EVENT IDENTIFIER - connects checklist & sightings
    Field('latitude'),      # LATITUDE - latitude of sighting
    Field('longitude'),     # LONGITUDE - longitude of sighting
    Field('date'),          # DATE - observation date
    Field('time'),          # TIME - time observations started
    Field('observer_id'),   # OBSERVER_ID - obseçrver ID, from checklist.csv
    Field('duration'),      # DURATION - duration of minutes of observations
    Field('user_id'),       # USER_ID - ID of user account, user needs to be logged in to enter a checklist and access personal checklist page
    Field('user_email')     # USER_EMAIL - email of user account, user needs to be logged in to enter a checklist and access personal checklist page
)
prime_checklists()

### SIGHTINGS DATABASE ###
# SAMPLING EVENT IDENTIFIER,COMMON NAME,OBSERVATION COUNT
db.define_table('sightings',
    Field('sei'),           # SAMPLING EVENT IDENTIFIER - connects checklist & sightings
    Field('specie'),        # SPECIE - common name of the specie
    Field('count'),         # COUNT - observation count
    Field('favorite', 'boolean', default=False),      # FAVORITE - our creative addition, whether it's a favorite of the user 
    Field('user_email')     # USER_EMAIL - email of user account, user needs to be logged in to enter a checklist and access personal checklist page
)
prime_sightings()

db.define_table('checklist_data',
    Field('specie'),
    Field('total_count', 'integer'),
    Field('input', 'integer', default=0)
)
prime_checklist_data()

## always commit your models to avoid problems later
db.commit()