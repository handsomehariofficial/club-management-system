from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college_club.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # student, club_leader, admin
    # Optional: Add relationships for convenience
    joined_events = db.relationship('EventParticipant', backref='student', lazy=True)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_photo = db.Column(db.String(200), nullable=True)  # Cover photo for the club
    leader = db.relationship('User', backref='led_clubs', lazy=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(100), nullable=True)  # Ensure this column exists
    # Other columns as needed
  # Event photo
    participants = db.relationship('EventParticipant', backref='event', lazy=True)
    club = db.relationship('Club', backref='events', lazy=True)

class EventParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('event_id', 'student_id', name='unique_event_participation'),)

class JoinRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False)  # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=db.func.now())
    

migrate = Migrate(app, db)
    
@app.cli.command('init-db')
def init_db():
    db.create_all()
    print('Database initialized.')

    admin_email = 'admin@example.com'
    admin_password = generate_password_hash('123123')  # Hash the password
    admin_role = 'admin'

    # Check if the admin user already exists
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user:
        admin_user = User(username="Admin", email=admin_email, password=admin_password, role=admin_role)
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created!")
    else:
        print("Admin user already exists.")

# Routes
@app.route('/')
def home():
    clubs = Club.query.all()
    return render_template('home.html', clubs=clubs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        # Debugging output to check the user and password hash
        if user:
            print(f"User found: {user.email}")
            print(f"Password hash: {user.password}")

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            elif user.role == 'club_leader':
                return redirect(url_for('club_leader_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))

        flash('Invalid email or password')

    return render_template('login_register.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = generate_password_hash(request.form['password'])
            role = 'student'  # Register as a student by default

            new_user = User(username=username, email=email, password=password, role=role)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now log in.')
            return redirect(url_for('login'))
        except KeyError as e:
            flash(f"Missing form field: {e}")
            return redirect(url_for('register'))
    return render_template('login_register.html')



@app.route('/student/dashboard', methods=['GET', 'POST'])
def student_dashboard():
    
    # Ensure user is logged in and has the 'student' role
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)


    # Handle form submissions
    if request.method == 'POST':
        # Handle join club request
        if 'club_id' in request.form:
            club_id = int(request.form['club_id'])
            existing_request = JoinRequest.query.filter_by(student_id=user_id, club_id=club_id).first()

            if existing_request:
                flash('You have already sent a request for this club.', 'warning')
            else:
                new_request = JoinRequest(student_id=user_id, club_id=club_id, status='Pending')
                db.session.add(new_request)
                db.session.commit()
                flash('Join request sent successfully!', 'success')

        # Handle event participation
        elif 'event_id' in request.form:
            event_id = int(request.form['event_id'])
            existing_participation = EventParticipant.query.filter_by(student_id=user_id, event_id=event_id).first()

            if existing_participation:
                flash('You are already participating in this event.', 'warning')
            else:
                new_participant = EventParticipant(student_id=user_id, event_id=event_id)
                db.session.add(new_participant)
                db.session.commit()
                flash('You have successfully joined the event!', 'success')

    # Fetch all clubs and events for the student dashboard
    clubs = Club.query.all()

    # Fetch IDs of clubs the student has joined or requested
    joined_club_ids = [
        req.club_id for req in JoinRequest.query.filter_by(student_id=user_id, status='Approved').all()
    ]
    requested_club_ids = [
        req.club_id for req in JoinRequest.query.filter_by(student_id=user_id).all()
    ]

    # Fetch all events (you can filter them by date or club if needed)
    events = Event.query.all()

    # Render the dashboard template with the fetched data
    return render_template(
        'student_dashboard.html',
        user=user,
        clubs=clubs,
        joined_club_ids=joined_club_ids,
        requested_club_ids=requested_club_ids,
        events=events
)



@app.route('/club_leader/dashboard', methods=['GET', 'POST'], endpoint='club_leader_dashboard')
def leader_dashboard():
    if 'user_id' not in session or session['role'] != 'club_leader':
        return redirect(url_for('login'))
    
    leader_id = session['user_id']
    club = Club.query.filter_by(leader_id=leader_id).first()

    if not club:
        flash('No club assigned to you.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle join requests
        if action in ['approve_request', 'reject_request']:
            request_id = request.form.get('request_id')
            if request_id and request_id.isdigit():
                join_request = JoinRequest.query.get(int(request_id))
                if join_request and join_request.club_id == club.id:
                    join_request.status = 'Approved' if action == 'approve_request' else 'Rejected'
                    db.session.commit()
                    flash(f'Request {"approved" if action == "approve_request" else "rejected"}.')
                else:
                    flash('Invalid join request.')
            else:
                flash('Invalid request ID.')

        # Remove members
        elif action == 'remove_member':
            member_id = request.form.get('member_id')
            if member_id and member_id.isdigit():
                join_request = JoinRequest.query.filter_by(
                    student_id=int(member_id), club_id=club.id, status='Approved'
                ).first()
                if join_request:
                    db.session.delete(join_request)
                    db.session.commit()
                    flash('Member removed successfully.')
                else:
                    flash('Invalid member ID.')
            else:
                flash('Invalid member ID.')

        # Update club information
        elif action == 'update_club':
            club_name = request.form.get('club_name', '').strip()
            club_description = request.form.get('club_description', '').strip()
            cover_photo = request.files.get('cover_photo')

            if not club_name or not club_description:
                flash('Club name and description cannot be empty.')
            else:
                club.name = club_name
                club.description = club_description

                if cover_photo:
                    filename = f"club_cover_{club.id}.jpg"
                    cover_photo.save(f"static/uploads/{filename}")
                    club.cover_photo = filename

                db.session.commit()
                flash('Club information updated successfully!')

        # Create a new event
        elif action == 'create_event':
            event_name = request.form.get('event_name').strip()
            event_description = request.form.get('event_description').strip()
            event_photo = request.files.get('event_photo')

            if not event_name or not event_description:
                flash('Event name and description cannot be empty.')
            else:
                new_event = Event(
                    club_id=club.id,
                    name=event_name,
                    description=event_description
                )
                if event_photo:
                    filename = f"event_photo_{club.id}_{event_name}.jpg"
                    event_photo.save(f"static/uploads/{filename}")
                    new_event.photo = filename

                db.session.add(new_event)
                db.session.commit()
                flash('Event created successfully!')

        # Update and delete events
        elif action == 'update_event':
            event_id = request.form.get('event_id')
            if event_id and event_id.isdigit():
                event = Event.query.get(int(event_id))
                if event and event.club_id == club.id:
                    event.name = request.form.get('name', '').strip()
                    event.description = request.form.get('description', '').strip()
                    if 'cover_photo' in request.files:
                        event_photo = request.files['cover_photo']
                        filename = f"event_photo_{club.id}_{event.id}.jpg"
                        event_photo.save(f"static/uploads/{filename}")
                        event.photo = filename
                    db.session.commit()
                    flash('Event updated successfully.')
                else:
                    flash('Invalid event.')
            else:
                flash('Invalid event ID.')

        elif action == 'delete_event':
            event_id = request.form.get('event_id')
            if event_id and event_id.isdigit():
                event = Event.query.get(int(event_id))
                if event and event.club_id == club.id:
                    db.session.delete(event)
                    db.session.commit()
                    flash('Event deleted successfully.')
                else:
                    flash('Invalid event.')
            else:
                flash('Invalid event ID.')

    # Fetch data for the dashboard
    join_requests = JoinRequest.query.filter_by(club_id=club.id, status='Pending').all()
    members = JoinRequest.query.filter_by(club_id=club.id, status='Approved').all()
    events = Event.query.filter_by(club_id=club.id).all()

    return render_template(
        'club_leader_dashboard.html',
        club=club,
        join_requests=join_requests,
        members=members,
        events=events
    )

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')

        # Handle club creation
        if action == 'create_club':
            club_name = request.form.get('club_name', '').strip()
            club_description = request.form.get('club_description', '').strip()
            leader_id = request.form.get('leader_id', '').strip()

            if not club_name or not club_description or not leader_id:
                flash('All fields are required to create a club.')
                return redirect(url_for('admin_dashboard'))

            if not leader_id.isdigit():
                flash('Leader ID must be a valid number.')
                return redirect(url_for('admin_dashboard'))

            leader = User.query.get(int(leader_id))
            if not leader or leader.role != 'club_leader':
                flash('Invalid or non-existent club leader.')
                return redirect(url_for('admin_dashboard'))

            if Club.query.filter_by(name=club_name).first():
                flash('A club with this name already exists.')
                return redirect(url_for('admin_dashboard'))

            new_club = Club(name=club_name, description=club_description, leader_id=int(leader_id))
            db.session.add(new_club)
            db.session.commit()
            flash(f'Club "{club_name}" created successfully!')

        # Handle club leader registration
        elif action == 'register_leader':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

            if not username or not email or not password:
                flash('All fields are required to register a leader.')
                return redirect(url_for('admin_dashboard'))

            if User.query.filter_by(email=email).first():
                flash('Email already registered.')
                return redirect(url_for('admin_dashboard'))

            new_leader = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                role='club_leader'
            )
            db.session.add(new_leader)
            db.session.commit()
            flash(f'Club leader "{username}" registered successfully!')

        # Handle club deletion
        elif action == 'delete_club':
            club_id = request.form.get('club_id', '').strip()
            club = Club.query.get(int(club_id))
            if club:
                db.session.delete(club)
                db.session.commit()
                flash(f'Club "{club.name}" deleted successfully!')
            else:
                flash('Club not found.')

        # Handle event deletion
        elif action == 'delete_event':
            event_id = request.form.get('event_id', '').strip()
            event = Event.query.get(int(event_id))
            if event:
                db.session.delete(event)
                db.session.commit()
                flash(f'Event "{event.name}" deleted successfully!')
            else:
                flash('Event not found.')

        # Handle user deletion
        elif action == 'delete_user':
            user_id = request.form.get('user_id', '').strip()
            user = User.query.get(int(user_id))
            if user:
                db.session.delete(user)
                db.session.commit()
                flash(f'User "{user.username}" deleted successfully!')
            else:
                flash('User not found.')

        # Handle role update
        elif action == 'update_role':
            user_id = request.form.get('user_id', '').strip()
            new_role = request.form.get('new_role', '').strip()
            user = User.query.get(int(user_id))
            if user and new_role in ['student', 'club_leader', 'admin']:
                user.role = new_role
                db.session.commit()
                flash(f'User "{user.username}" role updated to "{new_role}"!')
            else:
                flash('Invalid user or role.')

    # Fetch data for display
    clubs = Club.query.all()
    events = Event.query.all()
    users = User.query.all()
    club_leaders = User.query.filter_by(role='club_leader').all()

    return render_template('admin_dashboard.html', clubs=clubs, events=events, users=users, club_leaders=club_leaders)


# Approve/Reject Join Requests
@app.route('/join_request/<int:request_id>/<action>')
def handle_join_request(request_id, action):
    join_request = JoinRequest.query.get(request_id)
    if join_request:
        if action == 'approve':
            join_request.status = 'Approved'
        elif action == 'reject':
            join_request.status = 'Rejected'
        db.session.commit()
    return redirect(url_for('club_leader_dashboard'))

@app.route('/logout')
def logout():
    session.clear()  # Clears all session data
    return redirect(url_for('login'))  # Redirect to the login page



if __name__ == '__main__':
    app.run(debug=True)
