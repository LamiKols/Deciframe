# Sample Data for Bulk Import Testing

This directory contains sample CSV files for testing the bulk data import functionality in DeciFrame.

## Available Files

### Problems Sample Data (`sample_data_problems.csv`)
- **Fields**: title, description, priority, impact, urgency, status
- **Records**: 5 sample problem entries
- **Use Case**: Testing problem import with various priority levels and statuses

### Business Cases Sample Data (`sample_data_business_cases.csv`)
- **Fields**: title, summary, cost_estimate, benefit_estimate, case_type, status
- **Records**: 5 sample business case entries
- **Use Case**: Testing business case import with cost/benefit analysis

### Projects Sample Data (`sample_data_projects.csv`)
- **Fields**: name, description, budget, status, start_date, target_end_date
- **Records**: 5 sample project entries
- **Use Case**: Testing project import with dates and budget information

## How to Use

1. Navigate to **Admin → Bulk Data Import** in DeciFrame
2. Select the data type you want to import (Problems, Business Cases, or Projects)
3. Upload the corresponding CSV file
4. Map the columns to the system fields
5. Execute the import and review results

## File Format Notes

- All files use standard CSV format with headers in the first row
- Date fields use YYYY-MM-DD format
- Numeric fields (budgets, estimates) use plain numbers without currency symbols
- Text fields support multi-word descriptions and special characters