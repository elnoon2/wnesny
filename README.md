# Wnesny (ونسني)
### Interest-Based Ride-Sharing Platform

**More than a ride. A better company on the road.**

Wnesny is an interest-based ride-sharing web application that connects drivers and passengers traveling along compatible routes while considering shared interests, educational backgrounds, and personal preferences.

Unlike traditional ride-sharing platforms that primarily focus on transportation logistics, Wnesny aims to make compatibility an essential part of the journey.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Our Solution](#our-solution)
- [How Wnesny Works](#how-wnesny-works)
- [Core Features](#core-features)
- [AI-Based Compatibility Matching](#ai-based-compatibility-matching)
- [Web Application Pages](#web-application-pages)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Database Design](#database-design)
- [Privacy and Security](#privacy-and-security)
- [Project Status](#project-status)
- [Getting Started](#getting-started)
- [Academic Objectives](#academic-objectives)
- [Team](#team)
- [Documentation](#documentation)
- [License](#license)

---

## Overview

Wnesny (ونسني) is a web-based ride-sharing platform designed for the general public.

The platform allows users to publish available rides, discover journeys that match their destinations and schedules, and request to travel with other users.

What makes Wnesny different is its focus on **human compatibility**.

The platform aims to consider multiple factors when recommending potential ride matches:

- Route and destination compatibility.
- Departure time compatibility.
- Shared interests and hobbies.
- Optional educational background.
- Conversation preferences.

Wnesny aims to transform ordinary shared transportation into a more compatible, comfortable, and socially engaging experience.

**The platform is designed for everyone, not exclusively for university students.**

---

## Problem Statement

Traditional ride-sharing services primarily focus on transportation logistics, including pickup locations, destinations, availability, and pricing.

However, sharing a journey with someone involves more than simply traveling in the same direction.

Drivers and passengers may have different interests, communication preferences, and backgrounds. This can make shared journeys less comfortable or enjoyable, especially during long trips.

Wnesny addresses this gap by introducing compatibility-based recommendations into the ride-sharing experience.

## Our Solution

Wnesny combines ride-sharing functionality with an intelligent compatibility recommendation system.

Users create a single account and can participate in different journeys as either drivers or passengers.

The platform provides a structured experience where users can:

1. Publish rides and specify their travel details.
2. Search for rides matching their destinations and schedules.
3. Discover compatible ride recommendations.
4. Send ride requests to drivers.
5. Communicate after their requests are accepted.
6. Review each other after completing a journey.

The goal is to help people find not only a suitable ride, but also a suitable companion.

---

## How Wnesny Works

### 1. Create an Account

Users register and create a profile containing basic personal information, interests, and optional educational details.

Users can control the visibility of their educational information.

### 2. Offer a Ride

A driver publishes a ride by specifying:

- Starting location.
- Destination.
- Departure date and time.
- Additional ride information.

### 3. Find a Ride

Passengers explore available rides and discover options based on their travel requirements.

### 4. Discover Compatible Matches

Wnesny is designed to recommend suitable rides using route compatibility, departure time, shared interests, and optional profile information.

The system will also explain why a particular match is recommended.

### 5. Send a Ride Request

A passenger sends a request to join a ride.

The driver can review incoming requests and accept one passenger.

### 6. Start a Conversation

Once a request is accepted, a private conversation becomes available between the driver and the accepted passenger.

### 7. Complete and Review the Ride

After the journey is completed, both participants can leave reviews and ratings.

---

## Core Features

| Feature | Description |
|---|---|
| User Authentication | Account registration, login, and secure password handling |
| User Profiles | Personal information, interests, and optional education details |
| Interest Selection | Select interests from predefined categories |
| Offer a Ride | Publish a journey with origin, destination, and departure time |
| Find a Ride | Discover available rides |
| Compatibility Matching | Recommend rides based on multiple compatibility factors |
| Ride Requests | Request to join a ride and manage incoming requests |
| Request Management | Drivers accept or reject passenger requests |
| Private Chat | Communicate with accepted ride participants |
| Notifications | Receive updates about ride activities |
| Reviews and Ratings | Review participants after completing a journey |

---

## AI-Based Compatibility Matching

One of Wnesny's main objectives is to introduce an explainable compatibility recommendation system.

Unlike traditional location-based matching, Wnesny aims to evaluate multiple dimensions of compatibility.

### Matching Factors

**1. Route Compatibility**

Evaluates how well the passenger's travel requirements align with the driver's route.

**2. Departure Time**

Considers whether the proposed departure time fits the passenger's schedule.

**3. Shared Interests**

Identifies common interests and hobbies between users.

**4. Educational Compatibility**

Can consider optional educational information when users choose to share it.

**5. Conversation Preferences**

Considers whether users prefer a talkative, quiet, or flexible conversation environment.

### Explainable Recommendations

The system is intended to provide understandable reasons behind recommendations, such as:

- You share three common interests.
- Your destinations are compatible.
- Your departure times are close.
- You have similar conversation preferences.

The compatibility score is intended to support recommendations. It does not represent a person's safety, trustworthiness, or character.

> **Development note:** The AI matching engine is planned and has not yet been implemented in the current database-stage release.

---

## Web Application Pages

The planned web application is organized around the following pages:

| Page | Purpose |
|---|---|
| Landing Page | Introduce Wnesny and explain how it works |
| Register / Login | Create an account and access the platform |
| Dashboard | Display relevant rides, activity, and notifications |
| Find a Ride | Browse and search available rides |
| Offer a Ride | Publish a new journey |
| My Rides | Manage rides and ride requests |
| Ride Details | View journey information and participants |
| Request Management | Accept or reject incoming requests |
| Chat | Communicate with accepted ride participants |
| Profile | Manage personal information and interests |
| Notifications | View updates and ride-related activities |

---

## Technology Stack

Wnesny uses a Python-based backend and a lightweight web architecture.

| Layer | Technology |
|---|---|
| Programming Language | Python 3.12+ |
| Backend Framework | Flask 3 |
| ORM | SQLAlchemy 2 |
| Database Migrations | Flask-Migrate / Alembic |
| Database | SQLite (development and testing) |
| Future Database Support | PostgreSQL-compatible schema |
| Authentication Utilities | Flask-Login and Werkzeug |
| Frontend | HTML5, CSS3, JavaScript |
| UI Framework | Bootstrap 5 |
| Template Engine | Jinja2 |
| Testing | Pytest |
| Data Analysis | NumPy, pandas, SciPy, statsmodels, Matplotlib |

---

## System Architecture

Wnesny follows a modular Flask architecture using the Application Factory pattern.

The application separates its main responsibilities into independent components:

- **Models:** Define database entities and relationships.
- **Services:** Handle business logic and transactional operations.
- **Routes:** Handle HTTP requests and connect the frontend to backend services.
- **Templates:** Render the web application's user interface.
- **Static Assets:** Store CSS, JavaScript, and other frontend resources.
- **Migrations:** Manage database schema changes.

This structure keeps the application maintainable, organized, and easier to extend.

---

## Database Design

The current database foundation consists of ten main tables:

| Table | Responsibility |
|---|---|
| `users` | User accounts |
| `user_profiles` | User profiles and optional education information |
| `interests` | Predefined interest catalogue |
| `user_interests` | User-interest relationships |
| `rides` | Published journeys |
| `ride_requests` | Passenger requests |
| `conversations` | Conversations linked to accepted requests |
| `messages` | Chat messages |
| `reviews` | Post-ride reviews and ratings |
| `notifications` | User notifications |

### Important Business Rules

- One account can act as either a driver or passenger.
- A user cannot request their own ride.
- A ride can have at most one accepted passenger.
- Conversations are available only after request acceptance.
- Only conversation participants can access their messages.
- Cancelled rides preserve their history.
- Reviews are allowed only after ride completion.
- Users cannot review themselves.

The database uses constraints, foreign keys, indexes, and service-layer validation to maintain data integrity.

For more details, see [`docs/database-schema.md`](docs/database-schema.md).

---

## Privacy and Security

Privacy is an important part of Wnesny's design.

The application follows these principles:

- Passwords are stored as secure hashes, not plain text.
- Email addresses are normalized.
- Educational information is optional.
- Users can control the visibility of their educational information.
- Location coordinates are optional.
- The platform does not require continuous live GPS tracking.
- Private conversations are restricted to accepted ride participants.
- Database constraints help prevent invalid operations.

---

## Project Status

Wnesny is currently under active development.

| Component | Status |
|---|---|
| Flask Application Factory | Implemented |
| Application Configuration | Implemented |
| Database Models | Implemented |
| Database Relationships and Constraints | Implemented |
| Database Migrations | Implemented |
| Database Service Layer | Implemented |
| Interest Seed Data | Implemented |
| Database Tests | Implemented |
| Authentication and Sessions | Planned |
| Web Routes | Planned |
| Frontend Pages | Planned |
| AI Matching Engine | Planned |
| Synthetic Data Generation | Planned |
| Statistical Evaluation | Planned |
| Results Dashboard | Planned |

The current milestone focuses on establishing a reliable database foundation before proceeding with authentication, web interfaces, and intelligent matching.

---

## Getting Started

### Prerequisites

- Python 3.12 or later
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file:

**Windows:**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Configure the required environment variables when needed.

Never commit your `.env` file or secret keys to GitHub.

### 5. Apply Database Migrations

```bash
flask --app run.py db upgrade
```

### 6. Seed Initial Interests

```bash
python seed_interests.py
```

The seed script inserts 32 predefined interests across 8 categories.

### 7. Run Tests

```bash
python -m pytest
```

> These commands describe the current database-stage setup. The complete web application will be runnable as authentication, routes, and frontend components are implemented.

---

## Academic Objectives

**Integrated Mega Project — Fall 2026**

School of Computing and Data Science  
Badya University

Related Courses:

- AI 306
- CS 312
- CO 208

The academic proposal defines the following evaluation targets:

1. Improve the mean simulated trip-compatibility rating by at least 0.5 points compared with random matching across at least 1,000 simulated requests.
2. Satisfy hard matching constraints in at least 95% of generated matches.
3. Match at least 90% of feasible requests and rank 200 requests in under five seconds.
4. Deliver a working web application with at least four pages, a results dashboard, and an AI demonstration page usable by a non-technical person.

**These are project targets, not achieved results.**

---

## Team

| Name | Responsibility |
|---|---|
| Youssef Essam | Project Manager |
| Nour Elkassy | Data and Statistics Lead |
| Mohamed Osama | AI Lead |
| Toqa Waleed | Database and Web Development Lead |
| Nada Moataz | Quality Assurance and Documentation Lead |

---

## Documentation

Additional technical documentation is maintained in the `docs/` directory:

- [`docs/architecture.md`](docs/architecture.md) — System architecture and design decisions.
- [`docs/database-schema.md`](docs/database-schema.md) — Database schema and relationships.
- [`docs/testing.md`](docs/testing.md) — Testing strategy and results.
- [`docs/development-progress.md`](docs/development-progress.md) — Development progress.
- [`docs/proposal/`](docs/proposal/) — Academic project proposal.
- [`docs/ai_use_statement.md`](docs/ai_use_statement.md) — AI usage statement.

---

## License

This project is developed for academic purposes as part of the Integrated Mega Project at Badya University.

A formal license has not yet been selected.
