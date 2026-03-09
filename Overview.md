*1. Project Overview*
The *Insurance Quote Creation Tool* is a web-based internal platform that enables authorized users to:
Authenticate securely
Manage insurance companies
Manage insurance products
Generate quotes for clients
Export and share quotes (PDF/Email)
Sign out securely
*Purpose:* To streamline insurance quote generation and management for insurance agents and internal staff, providing a centralized, structured, and secure system.
---
## *2. Goals & Objectives*
Enable agents to create accurate insurance quotes quickly.
Centralize company and product management.
Secure access with role-based authentication.
Provide a clean and intuitive UI with a sidebar for easy navigation.
Maintain audit logs and secure client data.
---
## *3. User Roles*
RolePermissionsAdminFull access to all modules and user managementAgentCreate quotes, view companies & productsViewerView-only access
---
## *4. Core Modules*
### *4.1 Authentication*
Login with email & password
Password recovery
Role-based access
Session handling with JWT or Django session
### *4.2 Companies*
Add/Edit/Delete companies
Fields: Name, Logo, Email, Contact Number, Commission %, Status
Search, Filter & Pagination
### *4.3 Products*
Add/Edit/Delete products linked to a company
Fields: Product Name, Category, Base Premium, Tax %, Commission %, Coverage Details, Terms & Conditions, Status
Dynamic filtering by company
### *4.4 Get Quote*
Select Company → Select Product → Enter Client Details → Calculate Premium → Generate Quote
Fields for Client Details: Name, CNIC/ID, Email, Phone, DOB, Coverage Period
Premium Calculation: Base Premium + Add-ons + Tax – Discount = Final Premium
Generate Quote ID
Download PDF or Email quote
Save quote to database
### *4.5 Sign Out*
Secure logout and session clear
Redirect to login page
---
## *5. Database Design (Basic)*
### *Users Table*
```id | name | email | password_hash | role | status | created_at```
### *Companies Table*
```id | name | logo | contact_email | contact_number | commission | status | created_at```
### *Products Table*
```id | company_id | name | category | base_premium | tax_percentage | commission_percentage | status```
### *Quotes Table*
```id | quote_id | user_id | company_id | product_id | client_name | client_email | coverage_start | coverage_end | base_premium | tax | discount | final_premium | status | created_at```
---
## *6. UI Layout*
*Sidebar (Left Navigation):*
Dashboard
Companies
Products
Get Quote
Sign Out
*Main Content Area:*
Table views (Companies/Products/Quotes)
Modal forms for Add/Edit
Quote generation wizard
*Layout Example:*
```------------------------------------------------
| Sidebar        |        Top Bar             |
| Dashboard      | Page Title  | User Profile |
| Companies      |                             |
| Products       |        Main Content         |
| Get Quote      |                             |
| Sign Out       |                             |
------------------------------------------------```
---
## *7. Technology Stack*
LayerTechnologyBackendDjango / Django REST FrameworkFrontendReact (optional: Django templates for MVP)DatabasePostgreSQLAuthenticationJWT or Django SessionPDF GenerationReportLab / WeasyPrintDeploymentDocker + Nginx + Gunicorn
---
## *8. Security Considerations*
Passwords hashed using bcrypt
HTTPS for all connections
CSRF protection
Role-based access control
Input validation for forms
Audit logs for quote generation
---
## *9. Future Enhancements*
Multi-step quote wizard
Advanced premium calculation rules
Admin analytics dashboard
Quote status tracking (Pending, Approved, Issued)
E-sign integration
Multi-tenant / SaaS-ready architecture
API integration for partners