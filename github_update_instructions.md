# Step-by-Step GitHub Update Instructions

## Problem
The GitHub repository's app.py file is missing the SQLAlchemy Base class definition, causing:
`NameError: name 'Base' is not defined`

## Solution: Add 2 Missing Lines

### Step 1: Open GitHub File Editor
1. Click this link: https://github.com/LamiKols/Deciframe/edit/main/app.py
2. You should see the GitHub file editor with the current app.py content

### Step 2: Add Missing Import
Find this section near the top (around line 5):
```python
from flask import Flask, request, session
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from flask_login import LoginManager, current_user
```

Add this line after the other imports:
```python
from sqlalchemy.orm import DeclarativeBase
```

### Step 3: Add Missing Class Definition
Scroll down to find the line that says:
```python
# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
```

BEFORE that line, add these 2 lines:
```python
class Base(DeclarativeBase):
    pass
```

### Step 4: Save and Commit
1. Scroll to the bottom of the page
2. In the "Commit changes" section, add a commit message like: "Add missing Base class for SQLAlchemy"
3. Click "Commit changes"

## Expected Result
After saving, the file structure should look like:
```python
from flask import Flask, request, session
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  
from flask_login import LoginManager, current_user
from sqlalchemy.orm import DeclarativeBase    ← ADDED
import os
import logging
...

class Base(DeclarativeBase):    ← ADDED
    pass                        ← ADDED

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)  ← NOW WORKS
```

## Verification
1. Render will automatically detect the changes
2. The deployment should succeed within 2-3 minutes
3. The error "NameError: name 'Base' is not defined" will be resolved