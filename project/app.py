import qrcode
from io import BytesIO
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, make_response,flash
from pymongo import MongoClient
import datetime

app = Flask(__name__)
app.secret_key = '24d08376064529efdb372fda78870a4d'  # Set your own secret key

# MongoDB Connection
client = MongoClient('mongodb://localhost:27017/')
db = client.event_ticket_booking
booking_collection = db.bookings
users_collection = db.users
contact_collection = db.contacts

# Dummy data for events
events = [
    {'id': 1, 'name': 'LIVE CONCERT', 'date': '2024-10-01', 'location': 'Gachibowli', 'description': 'An amazing concert featuring top artists.', 'image': 'live.jpg', 'price': '100'},
    {'id': 2, 'name': 'MUSIC BAND', 'date': '2024-10-02', 'location': 'Film city', 'description': 'A thrilling concert with live performances.', 'image': 'instruments.jpg', 'price': '100'},
    {'id': 3, 'name': 'STANDUP COMEDY ', 'date': '2024-11-03', 'location': 'The comedy Theatre-HYD', 'description': 'Enjoy a night of classical music.', 'image': 'stand.jpg', 'price': '100'},
    {'id': 4, 'name': 'MUSICAL NIGHTS', 'date': '2024-11-04', 'location': 'Jubilee Hills', 'description': 'A conference on emerging technologies.', 'image': 'musical nyt.jpg', 'price': '100'},
    {'id': 5, 'name': 'COMEDY SHOW', 'date': '2024-10-05', 'location': 'Hydrabadass ComedyClub', 'description': 'Join us for discussions on the future of AI.', 'image': 'comedyshow.jpg', 'price': '100'},
    {'id': 6, 'name': 'DJ NIGHTS', 'date': '2024-10-06', 'location': 'Hydrabad', 'description': 'Hands-on workshop on web development.', 'image': 'djj.jpg', 'price': '100'},
]

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    buffered = BytesIO()
    img.save(buffered, format='PNG')
    buffered.seek(0)
    
    response = make_response(buffered.getvalue())
    response.headers.set('Content-Type', 'image/png')
    response.headers.set('Content-Disposition', 'inline; filename=qr_code.png')
    return response

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/events')
def events_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('events.html', events=events)

@app.route('/event/<int:event_id>')
def event_details(event_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    event = next((event for event in events if event['id'] == event_id), None)
    if not event:
        return redirect(url_for('events_page'))
    return render_template('event_details.html', event=event)

@app.route('/book/<int:event_id>', methods=['GET', 'POST'])
def book(event_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    event = next((event for event in events if event['id'] == event_id), None)
    if not event:
        return redirect(url_for('events_page'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        tickets = request.form.get('tickets')
        booking_details = f'Name: {name}, Email: {email}, Mobile: {mobile}, Tickets: {tickets}'

        # Save booking
        booking_collection.insert_one({
            'username': session['username'],
            'event_id': event_id,
            'details': booking_details,
            'timestamp': datetime.datetime.now()
        })
        return render_template('booking_confirmation.html', qr_code_url=url_for('qr_code', data=booking_details))
    return render_template('booking.html', event=event)

@app.route('/qr_code')
def qr_code():
    data = request.args.get('data')
    return generate_qr_code(data)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        
        if password != confirm_password:
            return "Passwords do not match", 400
        if users_collection.find_one({'username': username}):
            return "Username already exists", 400
        users_collection.insert_one({'username': username, 'password': password, 'role':role})
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users_collection.find_one({'username': username, 'password':password})
        if user:
             session['username'] = user['username']
             session['role'] = user['role']

             if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
             else:
                return redirect(url_for('user'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/manage_users')
def manage_users():
    # Fetch all bookings from the database
    bookings = booking_collection.find()
    return render_template('manage_users.html', bookings=bookings)
@app.route('/manage_contact')
def manage_contact():
    # Fetch all bookings from the database
    contacts = contact_collection.find()
    return render_template('manage_contact.html', contacts=contacts)

@app.route('/user')
def user():
    return render_template('home.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_bookings = booking_collection.find({'username': session['username']})
    return render_template('profile.html', username=session['username'], bookings=user_bookings, events=events)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/media')
def media():
    return render_template('media.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/contact_us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        message = request.form.get('message')
        
        contact_collection.insert_one({
            'username': username,
            'email': email,
            'message': message
        })
        
        return redirect(url_for('contact_us_success'))
    
    return render_template('contact_us.html')

@app.route('/contact_us_success')
def contact_us_success():
    return render_template('contact_us_success.html')



if __name__ == '__main__':
    app.run(debug=True)