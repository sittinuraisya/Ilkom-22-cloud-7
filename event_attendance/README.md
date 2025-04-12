# Event Attendance System

A fullstack application for managing event registrations and attendance tracking.

## Features
- User authentication (register/login)
- Event management (CRUD operations)
- Attendee registration and check-in
- Email verification
- Admin dashboard
- RESTful API

## Technologies
- **Backend**: Node.js, Express, MongoDB
- **Frontend**: React (to be implemented)
- **Authentication**: JWT
- **Email**: Nodemailer

## Installation

1. Clone the repository
2. Install dependencies:
```bash
npm install
```

3. Create `.env` file (use `.env.example` as template)
4. Start the development server:
```bash
npm run dev
```

## API Documentation

The API follows RESTful conventions with these endpoints:

- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/events` - Get all events
- `POST /api/v1/events` - Create new event (admin)
- `POST /api/v1/attendees/register/:eventId` - Register for event

## Environment Variables

See `.env.example` for required variables.

## License
MIT
