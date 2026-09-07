# NLAMS --- National Land Acquisition & Management System

> **Web-based platform for transparent, GIS-enabled land acquisition
> management**

**Smart India Hackathon 2026 · Team BhoomiSetu**

NLAMS is a Django-based prototype designed to digitize and centralize
the land acquisition lifecycle --- from project proposal and land
identification to compensation, rehabilitation & resettlement (R&R),
possession, monitoring, and reporting.

The system provides a single web interface for project agencies and
administrators to track acquisition activities, connect land parcels
with projects, visualize parcels geographically, monitor
compensation/R&R, and follow the acquisition workflow.

------------------------------------------------------------------------

## 🚀 Key Features

### 1. Command Dashboard

The NLAMS dashboard provides a consolidated operational view of the
current land acquisition portfolio.

It includes:

-   Total projects
-   Land required
-   Land acquired
-   Compensation paid
-   Affected families
-   Acquisition progress
-   Statutory lifecycle/workflow
-   Action-required indicators
-   Recent projects
-   GIS overview
-   Responsive desktop/tablet/mobile layout

Dashboard figures are designed to be driven by the Django database
rather than relying on hardcoded national statistics.

------------------------------------------------------------------------

### 2. Project Management

Project records can be created and tracked through the system.

Project information includes:

-   Project name
-   Project type
-   State
-   District
-   Land required
-   Project description
-   Acquisition status
-   Creation timestamp

Supported project statuses include:

-   Submitted
-   Under Review
-   Approved
-   Acquisition
-   Completed

------------------------------------------------------------------------

### 3. Land Parcel Management

NLAMS connects individual land parcels to their parent project.

Parcel records contain:

-   Parcel ID
-   Owner name
-   Area
-   Latitude
-   Longitude
-   Acquisition status
-   Project association
-   Optional parcel boundary geometry

Supported parcel statuses include:

-   Identified
-   Verified
-   Notified
-   Acquired
-   Possession Taken

This project-to-parcel relationship creates the foundation for
parcel-level monitoring and GIS visualization.

------------------------------------------------------------------------

### 4. GIS / Spatial Visualization

NLAMS includes an interactive GIS interface using **Leaflet** and
**OpenStreetMap**.

The GIS module supports:

-   Latitude/longitude based parcel positioning
-   Interactive map navigation
-   Parcel markers
-   Parcel boundary polygons
-   Parcel information popups
-   Acquisition-status visualization
-   Project/parcel spatial context
-   Responsive map display

The dashboard contains a simplified GIS overview, while the dedicated
GIS Map page provides the more detailed spatial interface.

#### Current prototype

The prototype uses:

-   Leaflet
-   OpenStreetMap
-   Browser-based geospatial visualization
-   Sample/demo parcel coordinates and boundaries

#### Future integration

The architecture can be extended to:

-   PostGIS
-   Official cadastral maps
-   Government land-record systems
-   Survey/cadastral APIs
-   GeoJSON services
-   State and district GIS portals

------------------------------------------------------------------------

### 5. Compensation Management

The compensation module tracks financial assessment and payment against
individual land parcels.

Each compensation record can contain:

-   Parcel
-   Assessed amount
-   Paid amount
-   Remaining amount
-   Payment status
-   Payment date
-   Remarks

Payment statuses:

-   Pending
-   Partially Paid
-   Fully Paid

The system can update a pending/partial compensation record through the
payment workflow.

Indian currency formatting is used for financial values.

------------------------------------------------------------------------

### 6. Rehabilitation & Resettlement (R&R)

The R&R module tracks affected/displaced families associated with a
project.

Records include:

-   Family ID
-   Family name
-   Displaced status
-   Rehabilitation status
-   Assistance amount
-   Remarks
-   Project association

Supported rehabilitation statuses:

-   Pending
-   In Progress
-   Completed

This allows project teams to monitor R&R progress alongside acquisition
and compensation.

------------------------------------------------------------------------

### 7. Possession Tracking

The possession module tracks the final physical possession stage for
acquired parcels.

Records include:

-   Parcel
-   Possession status
-   Possession date
-   Remarks
-   Creation timestamp

Supported statuses:

-   Pending
-   In Progress
-   Possession Taken

This connects parcel acquisition with the final possession stage of the
project lifecycle.

------------------------------------------------------------------------

### 8. End-to-End Workflow

NLAMS represents the acquisition lifecycle as a connected workflow:

``` text
Proposal
   ↓
Verification
   ↓
Approval
   ↓
Land Identification
   ↓
Notification
   ↓
Compensation
   ↓
R&R
   ↓
Possession
   ↓
Completion
```

The workflow interface provides a visual representation of the current
stage and pending actions.

------------------------------------------------------------------------

### 9. Reports & MIS

The Reports module provides a foundation for management information and
executive monitoring.

The system can be extended to generate reports around:

-   Project progress
-   Land acquisition
-   Parcel status
-   Compensation
-   R&R
-   Possession
-   Project timelines
-   District/state level monitoring

Future versions can add downloadable PDF/Excel reports, scheduled
reports, alerts, and richer MIS analytics.

------------------------------------------------------------------------

### 10. Authentication & User Access

NLAMS uses **Supabase Authentication** for the prototype login
experience, with Django maintaining the application-side session and
protected views.

The authentication flow includes:

``` text
User
  ↓
Supabase Login
  ↓
Authentication Token
  ↓
Django Session
  ↓
Protected NLAMS Modules
```

Protected application views use Django authentication decorators.

> **Prototype note:** the current prototype contains simplified JWT
> handling. Production deployment should perform complete token
> signature verification, secure session management, role-based
> permissions, and other security hardening.

------------------------------------------------------------------------

### 11. Multilingual Interface

NLAMS includes a language selector designed for Indian-language
accessibility.

The current interface includes:

-   English
-   Hindi
-   Assamese
-   Bengali
-   Tamil
-   Telugu

The project also includes integration planning for **Sarvam AI**
translation services.

The architecture can be extended to support additional Indian languages
and dynamic translation of dashboard/module content.

------------------------------------------------------------------------

## 🧩 Technology Stack

### Backend

  -----------------------------------------------------------------------
  Technology                          Purpose
  ----------------------------------- -----------------------------------
  **Python**                          Core programming language

  **Django**                          Web framework, routing, templates,
                                      authentication/session handling and
                                      business logic

  **SQLite**                          Prototype database

  **Django ORM**                      Database access and relationships

  **python-dotenv**                   Environment-variable configuration

  **Sarvam AI SDK**                   Indian-language translation
                                      integration
  -----------------------------------------------------------------------

### Frontend

  Technology          Purpose
  ------------------- -----------------------------------------
  **HTML5**           Page structure
  **CSS3**            Responsive UI and GovTech design system
  **JavaScript**      Client-side interactions
  **Leaflet**         Interactive GIS maps
  **OpenStreetMap**   Prototype map tiles
  **Chart.js**        Dashboard charts and visual analytics
  **Supabase JS**     Browser-side authentication

### Data / GIS

  Technology         Current / Future
  ------------------ ---------------------------------
  SQLite             Current prototype
  Django ORM         Current
  JSONField          Current parcel-boundary storage
  PostGIS            Production/future GIS database
  GeoJSON            Future spatial data exchange
  Cadastral APIs     Future government integration
  Land-record APIs   Future integration

------------------------------------------------------------------------

## 🏗️ System Architecture

``` text
                    ┌──────────────────────────┐
                    │        NLAMS UI          │
                    │ Desktop / Tablet / Mobile│
                    └────────────┬─────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
        ┌────────▼────────┐            ┌────────▼────────┐
        │ Django Templates │            │ JavaScript UI   │
        │ HTML / CSS       │            │ Leaflet/Charts  │
        └────────┬────────┘            └────────┬────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                         ┌───────▼────────┐
                         │ Django Backend │
                         │ Views / URLs   │
                         │ Business Logic │
                         └───────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │ Django ORM     │
                         └───────┬────────┘
                                 │
                   ┌─────────────▼─────────────┐
                   │        SQLite DB          │
                   │ Projects                  │
                   │ Land Parcels              │
                   │ Compensation              │
                   │ R&R                       │
                   │ Possession                │
                   └───────────────────────────┘

External / Future Services
────────────────────────────────────────────────
Supabase Authentication
Sarvam AI Translation
OpenStreetMap
Government Land Records / Cadastral APIs
PostGIS
```

------------------------------------------------------------------------

## 🗂️ Main Application Modules

``` text
NLAMS
│
├── Dashboard
│   ├── KPIs
│   ├── Acquisition Progress
│   ├── Workflow
│   ├── Action Required
│   ├── GIS Overview
│   └── Recent Projects
│
├── Projects
│   ├── Project List
│   ├── Project Details
│   └── Project Creation
│
├── Land Parcels
│   ├── Parcel Records
│   ├── Ownership
│   ├── Area
│   ├── Coordinates
│   └── Acquisition Status
│
├── GIS Map
│   ├── Parcel Markers
│   ├── Parcel Boundaries
│   ├── Status Visualization
│   └── Interactive Popups
│
├── Workflow
│   ├── Proposal
│   ├── Verification
│   ├── Approval
│   ├── Land Identification
│   ├── Notification
│   ├── Compensation
│   ├── R&R
│   ├── Possession
│   └── Completion
│
├── Compensation
│   ├── Assessment
│   ├── Payments
│   └── Payment Status
│
├── R&R
│   ├── Family Records
│   ├── Displacement
│   ├── Assistance
│   └── Rehabilitation Status
│
├── Possession
│   ├── Possession Records
│   ├── Status
│   └── Possession Date
│
└── Reports
    └── MIS / Monitoring
```

------------------------------------------------------------------------

## 🗄️ Core Data Model

The prototype is organized around five primary domain entities:

``` text
Project
   │
   ├────────── LandParcel
   │               │
   │               ├── Compensation
   │               └── Possession
   │
   └────────── RRCase
```

### Project

Represents an acquisition project.

### LandParcel

Represents an individual land parcel belonging to a project.

### Compensation

Represents financial assessment/payment associated with a parcel.

### RRCase

Represents rehabilitation and resettlement information for affected
families.

### Possession

Represents possession status for a parcel.

------------------------------------------------------------------------

## 📱 Responsive & Mobile-Ready Design

NLAMS is designed to work across:

-   Desktop
-   Laptop
-   Tablet
-   Mobile phones

The responsive UI uses:

-   CSS Grid
-   Flexbox
-   Responsive breakpoints
-   Fluid widths
-   Mobile navigation
-   Touch-friendly controls
-   Responsive cards
-   Responsive charts
-   Responsive GIS maps
-   Mobile-friendly forms
-   Vertical workflow presentation on smaller screens

The frontend is intentionally structured so that the major web screens
can later serve as the UX foundation for an Android/iOS application.

Possible future mapping:

``` text
Web Dashboard       → Mobile Dashboard
Projects            → Projects Screen
Project Details     → Project Screen
GIS Map             → GIS Screen
Workflow            → Workflow Screen
Compensation        → Compensation Screen
R&R                 → R&R Screen
Possession          → Possession Screen
Reports             → Reports Screen
```

------------------------------------------------------------------------

## 🔐 Configuration & Environment Variables

Sensitive credentials should be stored in `.env` and **must never be
committed to GitHub**.

Example:

``` env
SUPABASE_URL=your_supabase_project_url
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
SARVAM_API_KEY=your_sarvam_api_key
```

Keep `.env` in `.gitignore`:

``` gitignore
.env
venv/
__pycache__/
*.pyc
db.sqlite3
```

Never publish:

-   Supabase secret/service-role keys
-   Sarvam API keys
-   Passwords
-   Private credentials
-   Production database files

------------------------------------------------------------------------

## ⚙️ Local Installation

### 1. Clone the repository

``` bash
git clone https://github.com/adiprishi/NLAMS.git
cd NLAMS
```

### 2. Create a virtual environment

Windows:

``` powershell
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

``` bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

Install Django and the project's Python dependencies.

If a `requirements.txt` file is present:

``` bash
pip install -r requirements.txt
```

For the current prototype environment, the major Python packages
include:

``` bash
pip install django python-dotenv sarvamai
```

### 4. Configure environment variables

Create a `.env` file in the project root:

``` env
SUPABASE_URL=your_supabase_url
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
SARVAM_API_KEY=your_sarvam_api_key
```

### 5. Apply migrations

``` bash
python manage.py migrate
```

### 6. Create an admin user

``` bash
python manage.py createsuperuser
```

### 7. Start the development server

``` bash
python manage.py runserver
```

Open:

``` text
http://127.0.0.1:8000/
```

Admin:

``` text
http://127.0.0.1:8000/admin/
```

------------------------------------------------------------------------

## 🧪 Prototype Scope

This repository is an **SIH prototype**, not a production government
deployment.

### Implemented prototype capabilities

-   Django web application
-   Project management
-   Land parcel management
-   Parcel boundary storage
-   GIS map visualization
-   Compensation tracking
-   R&R tracking
-   Possession tracking
-   Project workflow
-   Dashboard analytics
-   Reports module
-   Supabase authentication
-   Responsive UI
-   Indian-language selector
-   Sarvam AI integration foundation

### Future production capabilities

The following are architectural extensions rather than claims of current
deployment:

-   Official land-record API integration
-   Official cadastral-map integration
-   PostGIS spatial database
-   Advanced role-based access control
-   Government identity integration
-   Secure document repository
-   Document version control
-   Complete audit trail
-   Digital signatures
-   Field/mobile application
-   Automated notifications
-   Timeline alerts
-   State/district/central dashboards
-   Advanced MIS exports
-   Production-grade API gateway
-   Security hardening and token verification
-   Cloud deployment and scalability

------------------------------------------------------------------------

## 🌐 API & Integration Roadmap

NLAMS is designed to become an integration layer between acquisition
stakeholders and external systems.

Potential integrations:

``` text
                    NLAMS
                      │
       ┌──────────────┼──────────────┐
       │              │              │
 Land Records      Cadastral       Identity
    APIs             GIS             APIs
       │              │              │
       └──────────────┼──────────────┘
                      │
               Compensation
                 / R&R / MIS
```

Potential future technologies:

-   Django REST Framework
-   REST APIs
-   PostGIS
-   GeoJSON
-   Government land-record APIs
-   Cadastral services
-   Secure document APIs
-   Notification services

------------------------------------------------------------------------

## 💡 Innovation

NLAMS combines multiple acquisition activities into one connected
operational workflow.

### Key innovation areas

**1. Project-to-parcel linkage**

Instead of treating acquisition records as isolated entries, NLAMS
connects projects directly with their land parcels.

**2. Spatial + operational monitoring**

GIS information is combined with workflow, compensation, R&R, and
possession status.

**3. Lifecycle visibility**

The complete acquisition journey can be monitored from proposal through
possession.

**4. Action-oriented dashboard**

The dashboard surfaces records that require attention rather than only
displaying historical information.

**5. Mobile-ready architecture**

The responsive interface is designed around reusable components that can
become the foundation for a future mobile application.

**6. Indian-language accessibility**

The system is designed with Indian-language translation support using
Sarvam AI.

------------------------------------------------------------------------

## 🎯 Expected Impact

NLAMS aims to improve:

-   Transparency
-   Accountability
-   Inter-agency coordination
-   Project monitoring
-   Parcel-level visibility
-   Compensation tracking
-   R&R monitoring
-   Possession tracking
-   Decision-making
-   Reporting efficiency

The long-term objective is to provide a centralized digital foundation
for faster, more transparent, and more people-centric land acquisition
management.

------------------------------------------------------------------------

## 🛣️ Roadmap

### Phase 1 --- Prototype

-   [x] Django application
-   [x] Project management
-   [x] Land parcel management
-   [x] GIS visualization
-   [x] Compensation
-   [x] R&R
-   [x] Possession
-   [x] Workflow
-   [x] Dashboard
-   [x] Reports
-   [x] Authentication
-   [x] Responsive UI

### Phase 2 --- Integration

-   [ ] REST API layer
-   [ ] Official land-record integration
-   [ ] Cadastral integration
-   [ ] PostGIS
-   [ ] Advanced roles and permissions
-   [ ] Document management
-   [ ] Audit history
-   [ ] Digital signatures

### Phase 3 --- National Scale

-   [ ] State/district/central dashboards
-   [ ] Field mobile application
-   [ ] Automated notifications
-   [ ] Timeline monitoring
-   [ ] Advanced MIS
-   [ ] Production cloud deployment
-   [ ] Inter-agency data exchange

------------------------------------------------------------------------

## 👥 Team

**Team TerraSync**

**Project:** NLAMS --- National Land Acquisition & Management System

**Event:** Smart India Hackathon 2026

------------------------------------------------------------------------

## 📄 Disclaimer

NLAMS is an academic/hackathon prototype created for demonstration and
evaluation.

Demo data shown in the application should not be interpreted as official
Government of India statistics, official land records, or evidence of
national deployment.

Government-system integrations described in the roadmap represent
proposed future capabilities.

------------------------------------------------------------------------

## 📜 License

This project is currently developed as a Smart India Hackathon
prototype.

Add an appropriate open-source or institutional license before public
production/open-source distribution.
