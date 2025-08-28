"""
Waitlist Routes for DeciFrame
Handles waitlist form submissions and management
"""

from flask import render_template, request, redirect, url_for, flash
from . import waitlist_bp
from models import Waitlist, db
from forms import WaitlistForm


@waitlist_bp.route('/', methods=['GET', 'POST'])
def index():
    """Handle waitlist signup form - main entry point"""
    form = WaitlistForm()
    
    if form.validate_on_submit():
        try:
            # Check if email already exists
            existing = Waitlist.query.filter_by(email=form.email.data).first()
            if existing:
                flash('Thank you! Your email is already on our waitlist.', 'info')
                return redirect(url_for('thank_you'))
            
            # Create new waitlist entry with proper field mapping
            full_name = f"{form.first_name.data} {form.last_name.data}".strip()
            waitlist_entry = Waitlist(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                name=full_name,  # Legacy field
                email=form.email.data,
                company=form.company.data or None,
                role=form.role.data or None,
                company_size=form.company_size.data or None,
                use_case=form.use_case.data or None,
                message=form.use_case.data or None,  # Legacy field alias
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500]
            )
            
            db.session.add(waitlist_entry)
            db.session.commit()
            
            print(f"✓ New waitlist signup: {full_name} <{form.email.data}> from {form.company.data or 'Unknown Company'}")
            return redirect(url_for('thank_you'))
            
        except Exception as e:
            print(f"❌ Waitlist signup error: {e}")
            db.session.rollback()
            flash('Sorry, there was an error processing your request. Please try again.', 'error')
    
    # GET request or form validation failed - show waitlist form
    return render_template('waitlist.html', form=form)


@waitlist_bp.route('/submit', methods=['POST'])
def submit():
    """Handle waitlist form submission - explicit submit endpoint"""
    return index()  # Redirect to main handler