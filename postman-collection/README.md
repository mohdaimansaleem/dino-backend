# Dino Backend API Postman Collection

This directory contains the complete Dino Backend API Postman collection broken down into manageable files.

## 📁 File Structure

- `01-collection-info.json` - Collection metadata, auth, and variables
- `02-authentication.json` - Authentication endpoints
- `03-workspaces.json` - Workspace management
- `04-venues.json` - Venue operations
- `05-users.json` - User management
- `06-tables.json` - Table management
- `07-menu.json` - Menu categories and items
- `08-orders.json` - Order management
- `09-public-ordering.json` - QR code ordering
- `10-dashboard-analytics.json` - Dashboard and analytics
- `11-system-health.json` - System health checks
- `12-testing-demo.json` - Testing and demo utilities
- `13-mobile-support.json` - Mobile app support
- `14-notifications.json` - Notification system
- `15-payments-billing.json` - Payment processing
- `16-reports.json` - Reporting system

## 🔧 Assembly Instructions

### Option 1: Using Node.js Script (Recommended)
```bash
cd postman-collection
node assemble-collection.js
```

### Option 2: Manual Assembly
1. Start with the structure from `01-collection-info.json`
2. Add each section (02-16) to the `item` array
3. Save as a complete Postman collection file

## 📋 Collection Features

- **🔐 Bearer Token Authentication** - Automatically managed
- **📝 Environment Variables** - Pre-configured for easy testing
- **🧪 Test Scripts** - Auto-capture response data
- **📊 Complete API Coverage** - All endpoints included
- **🎯 Demo Data** - Ready-to-use sample requests

## 🚀 Usage

1. Import the assembled collection into Postman
2. Set your `base_url` variable (default: `http://localhost:8000/api/v1`)
3. Start with Authentication → Register Workspace
4. Use the auto-captured tokens for subsequent requests

## 📊 Collection Stats

- **16 Major Sections**
- **80+ API Endpoints**
- **Complete CRUD Operations**
- **Authentication Flow**
- **Public API Support**

## 🔗 Quick Start Workflow

1. **Register Workspace** - Creates workspace, venue, and user
2. **Create Tables** - Set up table structure
3. **Create Menu** - Add categories and items
4. **Test Ordering** - Place and manage orders
5. **Analytics** - View reports and dashboard data

## 📱 Mobile & QR Support

The collection includes endpoints for: