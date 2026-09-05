# NLAMS — National Land Acquisition & Management System

A web-based prototype for digitizing and monitoring the end-to-end land acquisition process.

## 📌 About the Project

The National Land Acquisition & Management System (NLAMS) is a centralized web platform designed to improve transparency, accountability, monitoring, and coordination throughout the land acquisition process.

The system provides a digital workflow from project proposal and land identification to compensation, rehabilitation & resettlement, and final possession.

## 🎯 SIH Problem Statement

The proposed system addresses the need for a centralized digital platform for managing land acquisition activities across different stages and stakeholders.

Key objectives include:

- Digitizing the land acquisition workflow
- Tracking project progress and approval status
- Managing land parcels and ownership information
- Providing GIS-based spatial visualization
- Monitoring compensation assessment and payments
- Tracking Rehabilitation & Resettlement (R&R)
- Recording possession of acquired land
- Providing dashboards and reports for monitoring and decision-making
- Improving transparency and reducing delays

## 🚀 Current Features

### 📊 Dashboard
- Total projects
- Total land
- Compensation paid
- Recent projects

### 📁 Project Management
- Create new projects
- View project details
- Track project status
- Update acquisition workflow status

### 🗺️ Land Parcel Management
- Add land parcels
- Record parcel ID and owner
- Store land area
- Store latitude and longitude
- Track acquisition status

### 🌍 GIS Map
- Visualize land parcels geographically
- Display parcel locations using latitude and longitude

### 💰 Compensation
- Record assessed compensation
- Track amount paid
- Track pending, partial, and fully paid status
- Record payment dates and remarks

### 🏠 Rehabilitation & Resettlement
- Register affected families
- Track displaced families
- Track rehabilitation status
- Record assistance amounts and remarks

### 📍 Possession
- Record possession status
- Record possession date
- Track possession of individual land parcels
- Store possession remarks

### 🔐 Administration
- Django-based admin interface
- Database-backed management of system records

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Django | Web framework |
| SQLite | Prototype database |
| HTML/CSS | Frontend |
| JavaScript | Frontend functionality |
| Leaflet | GIS mapping |
| OpenStreetMap | Map data |

## 🔄 Acquisition Workflow

```text
Project Proposal
       ↓
Land Identification
       ↓
Land Verification
       ↓
Notification
       ↓
Compensation
       ↓
Rehabilitation & Resettlement
       ↓
Possession
       ↓
Project Completion