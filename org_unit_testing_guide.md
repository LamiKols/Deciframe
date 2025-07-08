# Organizational Unit Integration Testing Guide

## Testing Steps for DeciFrame Organizational Unit Integration

### 1. Test Problem Creation with Organizational Units
1. Navigate to Problems → New Problem
2. Fill out the problem form
3. Check that "Organizational Unit" dropdown is present
4. Select an organizational unit (e.g., "Information Technology" or "Frontend Development")
5. Submit the problem
6. Verify the problem is created and shows the assigned organizational unit

### 2. Test Business Case Creation with Organizational Units
1. Navigate to Business Cases → New Business Case
2. Fill out the business case form
3. Check that "Organizational Unit" field is present in the form
4. Select an organizational unit from the dropdown
5. Submit the business case
6. Verify in the business cases listing that the organizational unit column displays correctly

### 3. Test Project Creation with Organizational Units
1. Navigate to Projects → New Project
2. Fill out the project form
3. Check that "Organizational Unit" field is present
4. Select an organizational unit
5. Submit the project
6. Verify the project listing shows the organizational unit in the table

### 4. Test Filtering by Organizational Units
1. Go to Problems listing page
2. Use the filter dropdown for "Organizational Unit"
3. Select a specific unit and apply filter
4. Verify only problems assigned to that unit are displayed

5. Repeat filtering test for Business Cases and Projects pages

### 5. Test Admin Organizational Structure Management
1. Log in as admin (admin@deciframe.com / admin123)
2. Navigate to Admin → Organizational Structure
3. Verify the organizational chart displays correctly
4. Test clicking on organizational units to edit them
5. Test creating new organizational units
6. Test the CSV import functionality

### Expected Results
- All forms should include organizational unit selection
- All listing pages should display organizational unit information
- Filtering should work across all modules
- Admin interface should allow full CRUD operations on organizational structure