# Event RSVP Manager

A comprehensive web application for managing event RSVPs with features like one-click RSVP, automatic reminders, QR codes, and detailed analytics.

## Features

✅ **One-click RSVP** – Guests can confirm their attendance instantly, with no account needed  
✅ **Automatic reminders** – Sends alerts to ensure guests don't forget to RSVP or attend  
✅ **Easy updates** – Attendees can change their response or meal preference anytime  
✅ **Organizer dashboard** – A clear and organized way to track RSVPs and guest details  
✅ **QR codes and links** – Makes it easy to share invitations  
✅ **Guest insights** – Helps organizers understand RSVP trends for better planning  

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-Mail
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Email**: Flask-Mail with SMTP
- **Scheduling**: APScheduler for automatic reminders
- **QR Codes**: qrcode library

## Installation

### Prerequisites

- Python 3.8+
- MySQL database
- SMTP email service (Gmail, SendGrid, etc.)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Event-RSVP-Manager
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create environment file**
   Create a `.env` file in the root directory with the following variables:
   ```env
   # Database Configuration
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=rsvp_manager

   # Admin Configuration
   ADMIN_PASSWORD=your_admin_password

   # Email Configuration
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USE_SSL=false
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   MAIL_DEFAULT_SENDER=your_email@gmail.com
   ```

4. **Set up the database**
   - Create a MySQL database named `rsvp_manager`
   - The application will automatically create tables on first run

5. **Run the application**
   ```bash
   python app.py
   ```

## Usage

### For Organizers

1. **Register/Login**: Create an account or login with existing credentials
2. **Create Events**: Set up events with details, custom fields, and RSVP settings
3. **Add Guests**: Invite guests by email - they'll receive automatic invitations
4. **Manage RSVPs**: View responses, send reminders, and track attendance
5. **Analytics**: Monitor response rates and guest insights

### For Guests

1. **Receive Invitation**: Get an email with a unique RSVP link
2. **One-click RSVP**: Click the link and respond instantly (no account needed)
3. **Update Response**: Modify your RSVP or meal preferences anytime
4. **QR Code**: Use the QR code for easy access to your RSVP page

## Email Setup

### Gmail Setup
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password
3. Use the App Password in your `.env` file

### Other SMTP Providers
Update the `MAIL_SERVER`, `MAIL_PORT`, and other settings in your `.env` file according to your provider's specifications.

## Deployment

### Production Considerations

1. **Environment Variables**: Ensure all sensitive data is in environment variables
2. **Database**: Use a production MySQL database
3. **Email**: Configure a reliable SMTP service
4. **Static Files**: Serve static files through a web server (nginx)
5. **WSGI**: Use a production WSGI server (gunicorn, uwsgi)

### Example Deployment with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:create_app()
```

## Project Structure

```
Event-RSVP-Manager/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── models.py             # Database models
├── routes.py             # Flask routes and views
├── reminder.py           # Email reminder system
├── qr_generator.py       # QR code generation
├── analytics.py          # Analytics and reporting
├── requirements.txt      # Python dependencies
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
└── README.md            # This file
```

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Events
- `GET /dashboard` - Organizer dashboard
- `GET /event/create` - Create event form
- `POST /event/create` - Create new event
- `GET /event/<id>` - View event details
- `GET /event/<id>/edit` - Edit event form
- `POST /event/<id>/edit` - Update event

### Guests
- `GET /event/<id>/guests` - Manage guest list
- `POST /event/<id>/guests` - Add new guest
- `POST /event/<id>/guests/remind` - Send bulk reminders

### RSVP
- `GET /rsvp/<token>` - Guest RSVP page
- `POST /rsvp/<token>` - Submit RSVP response

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support or questions, please open an issue in the repository.
