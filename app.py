#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, abort, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import collections
collections.Callable = collections.abc.Callable
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String())
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venues', cascade='all, delete-orphan', lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artists', cascade='all, delete-orphan', lazy=True )


    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer(), primary_key=True)
    venue_id = db.Column(db.Integer(), db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer(), db.ForeignKey('Artist.id'), nullable=False)
    show_time = db.Column(db.DateTime, nullable=False)



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  my_data = []
  # Get Location Data
  location = db.session.query(Venue.state, Venue.city).all()

  for l in location:
    locations = {
      'state': l.state,
      'city': l.city,
      'venues': [],
    }

    if locations not in my_data:
      my_data.append(locations)
  
  # Get locations.venues data
  venue = db.session.query(Venue.id, Venue.name, Venue.city).all()

  for v in venue:
    venue_obj = {
      'id': v.id,
      'name': v.name,
      'num_upcoming_shows': 0 
    }
#Get upcoming shows
    upcoming_shows = Show.query.filter_by(venue_id=v.id).all()
    shows = []
    for i in upcoming_shows:
      up_shows = {
        'id':i.venue_id,
        'start_time':i.show_time
      }
      shows.append(up_shows)

    num_of_upcoming_shows = 0

    for i in shows:
      if i['id'] == v.id and i['start_time'] > datetime.now():
        num_of_upcoming_shows += 1
    venue_obj['num_upcoming_shows'] = num_of_upcoming_shows
  
    for data in my_data:
      if data['city'] == v.city:
        data['venues'].append(venue_obj)
  return render_template('pages/venues.html', areas=my_data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  venue = Venue.query.filter(Venue.name.ilike('%' +search_term+ '%')).all()

  response = {
    'count': len(list(venue)),
    'data': []
  }
  for v in venue:
    data = {
      'id': v.id,
      'name': v.name,
    }

    shows = Show.query.filter_by(venue_id=v.id)
    count = 0
    for i in shows:
      if i.show_time > datetime.now():
        count +=1
    data['num_upcoming_shows'] = count
    response['data'].append(data)

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  my_data=[]
  upcoming = []
  past = []
  past_count = 0
  upcoming_count = 0
  query = Venue.query.filter_by(id=venue_id).all()
  shows = Show.query.filter_by(venue_id=venue_id).all()

  for s in shows:
      if s.show_time < datetime.now():
        past_count += 1
        artist = Artist.query.filter_by(id=s.artist_id).all()
        for a in artist:
          result = {
          "artist_id": a.id,
          "artist_name": a.name,
          "artist_image_link": a.image_link,
          "start_time": s.show_time.strftime("%m/%d/%Y, %H:%M:%S")
          }
          past.append(result)
      else:
        upcoming_count += 1
        artist = Artist.query.filter_by(id=s.artist_id).all()
        for a in artist:
          result = {
          "artist_id": a.id,
          "artist_name": a.name,
          "artist_image_link": a.image_link,
          "start_time": s.show_time.strftime("%m/%d/%Y, %H:%M:%S")
          }
          upcoming.append(result)

  for v in query:
    result = {
    "id": v.id,
    "name": v.name,
    "genres": v.genres.split(','),
    "address": v.address,
    "city": v.city,
    "state": v.state,
    "phone": v.phone,
    "website": v.website,
    "facebook_link": v.facebook_link,
    "seeking_talent": v.seeking_talent,
    "seeking_description": v.seeking_description,
    "image_link": v.image_link,
    "past_shows": past,
    "upcoming_shows": upcoming,
    "past_shows_count": past_count,
    "upcoming_shows_count": upcoming_count,
    }
    
    my_data.append(result)
  return render_template('pages/show_venue.html', venue=my_data[0])

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
    new_venue = VenueForm(request.form)
    try:
        venue = Venue(
          name=new_venue.name.data,
          state=new_venue.state.data,
          city=new_venue.city.data,
          address=new_venue.address.data,
          phone=new_venue.phone.data,
          genres=','.join(new_venue.genres.data),
          image_link=new_venue.image_link.data,
          facebook_link=new_venue.facebook_link.data,
          website=new_venue.website_link.data,
          seeking_talent=new_venue.seeking_talent.data,
          seeking_description=new_venue.seeking_description.data
        )
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('Venue ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()
    return redirect(url_for('venues'))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  venue = Venue.query.filter_by(id=venue_id)
  try:
    db.session.delete(venue_id)
    db.session.commit()
    flash('Successfully deleted {}'.format(venue.name))

  except:
    error = True
    db.session.rollback()
    flash('Error deleting {}'.format(venue.name))
  finally:
    if error:
      abort(400)
    else:
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
      return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  query_artists = db.session.query(Artist.id, Artist.name).all()

  for artist in query_artists:
    artist = {
    "id": artist.id,
    "name": artist.name,
    }
    data.append(artist)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term', '')
  artist = Artist.query.filter(Artist.name.ilike('%' +search_term+ '%')).all()

  response = {
    'count': len(list(artist)),
    'data': []
  }
  for a in artist:
    data = {
      'id': a.id,
      'name': a.name,
    }

    shows = Show.query.filter_by(artist_id=a.id)
    count = 0
    for i in shows:
      if i.show_time > datetime.now():
        count +=1
    data['num_upcoming_shows'] = count
    response['data'].append(data)

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  my_data=[]
  upcoming = []
  past = []
  past_count = 0
  upcoming_count = 0
  query = Artist.query.filter_by(id=artist_id).all()
  shows = Show.query.filter_by(artist_id=artist_id).all()

  for s in shows:
      if s.show_time < datetime.now():
        past_count += 1
        venue = Venue.query.filter_by(id=s.venue_id).all()
        for v in venue:
          result = {
          "venue_id": v.id,
          "venue_name": v.name,
          "venue_image_link": v.image_link,
          "start_time": s.show_time.strftime("%m/%d/%Y, %H:%M:%S")
          }
          past.append(result)
      else:
        upcoming_count += 1
        venue = Venue.query.filter_by(id=s.venue_id).all()
        for v in venue:
          result = {
          "venue_id": v.id,
          "venue_name": v.name,
          "venue_image_link": v.image_link,
          "start_time": s.show_time.strftime("%m/%d/%Y, %H:%M:%S")
          }
          upcoming.append(result)

  for artist in query:
    print(artist.genres.split(","))
    result = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres.split(','),
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past,
    "upcoming_shows": upcoming,
    "past_shows_count": past_count,
    "upcoming_shows_count": upcoming_count,
    }
    
    my_data.append(result)

  return render_template('pages/show_artist.html', artist=my_data[0])

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm(request.form)
  query = Artist.query.get(artist_id)
  
  artist = {
    "id": query.id,
    "name": query.name,
    "genres": query.genres.split(','),
    "city": query.city,
    "state": query.state,
    "phone": query.phone,
    "website": query.website,
    "facebook_link": query.facebook_link,
    "seeking_venue": query.seeking_venue,
    "seeking_description": query.seeking_description,
    "image_link": query.image_link,
  }

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  try:
      artist = {
          "name":form.name.data,
          "state":form.state.data,
          "city":form.city.data,
          "phone":form.phone.data,
          "genres":','.join(form.genres.data),
          "image_link":form.image_link.data,
          "facebook_link":form.facebook_link.data,
          "website":form.website_link.data,
          "seeking_venue":form.seeking_venue.data,
          "seeking_description":form.seeking_description.data
      }
      Artist.query.filter_by(id=artist_id).update(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
      db.session.rollback()
      print(sys.exc_info())
       # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
      flash('Artist ' + request.form['name'] + ' could not be updated.')
  finally:
      db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  query = Venue.query.get(venue_id)
  
  venue = {
    "id": query.id,
    "name": query.name,
    "genres": query.genres.split(','),
    "address": query.address,
    "city": query.city,
    "state": query.state,
    "phone": query.phone,
    "website": query.website,
    "facebook_link": query.facebook_link,
    "seeking_talent": query.seeking_talent,
    "seeking_description": query.seeking_description,
    "image_link": query.image_link,
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    venue = VenueForm(request.form)
    try:
        venue = {
          "name":venue.name.data,
          "state":venue.state.data,
          "city":venue.city.data,
          "address":venue.address.data,
          "phone":venue.phone.data,
          "genres":','.join(venue.genres.data),
          "image_link":venue.image_link.data,
          "facebook_link":venue.facebook_link.data,
          "website":venue.website_link.data,
          "seeking_talent":venue.seeking_talent.data,
          "seeking_description":venue.seeking_description.data
        }        
        Venue.query.filter_by(id=venue_id).update(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('Venue ' + request.form['name'] + ' could not be updated.')
    finally:
      db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  try:
      artist = Artist(
          name=form.name.data,
          state=form.state.data,
          city=form.city.data,
          phone=form.phone.data,
          genres=','.join(form.genres.data),
          image_link=form.image_link.data,
          facebook_link=form.facebook_link.data,
          website=form.website_link.data,
          seeking_venue=form.seeking_venue.data,
          seeking_description=form.seeking_description.data
        )
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
      db.session.rollback()
      print(sys.exc_info())
       # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
      flash('Artist ' + request.form['name'] + ' could not be listed.')
  finally:
      db.session.close()
  return redirect(url_for('artists'))
 
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = db.session.query(Show).all()
  
  data = []
  for show in shows:
    result = {
    "venue_id": show.venues.id,
    "venue_name": show.venues.name,
    "artist_id": show.artists.id,
    "artist_name": show.artists.name,
    "artist_image_link": show.artists.image_link,
    "start_time": show.show_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    data.append(result)
  
  
  # for show in shows:
  #   artist = Artist.query.filter_by(id=show.artist_id)
  #   venue = Venue.query.filter_by(id=show.venue_id)
    
  #   result = {
  #   "venue_id": venue[0].id,
  #   "venue_name": venue[0].name,
  #   "artist_id": artist[0].id,
  #   "artist_name": artist[0].name,
  #   "artist_image_link": artist[0].image_link,
  #   "start_time": show.show_time.strftime("%m/%d/%Y, %H:%M:%S")
  #   }
  #   data.append(result)
   
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  artist_id = request.form.get('artist_id')
  venue_id = request.form.get('venue_id')
  show_time = request.form.get('start_time')

  try:
    show = Show(
      artist_id=artist_id,
      venue_id=venue_id,
      show_time=show_time
    )
    db.session.add(show)
    db.session.commit()
      # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
     db.session.rollback()
     print(sys.exc_info())
       # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
     flash('An error occurred. Show could not be listed.')
  finally:
      db.session.close()
  return redirect(url_for('shows'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
