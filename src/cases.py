from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from src.models import Case, Suspect, CaseUpdate, Officer
from src.forms import CaseForm, SuspectForm
import os
from datetime import datetime
from werkzeug.utils import secure_filename

cases_bp = Blueprint('cases', __name__)

@cases_bp.route('/cases')
@login_required
def view_cases():
    """View all cases based on role"""
    page = request.args.get('page', 1, type=int)
    
    if current_user.role in ['admin', 'supervisor']:
        cases = Case.query.filter(Case.status != 'archived')\
                          .order_by(Case.created_at.desc())\
                          .paginate(page=page, per_page=10)
    else:
        cases = Case.query.filter_by(assigned_officer_id=current_user.id)\
                          .filter(Case.status != 'archived')\
                          .order_by(Case.created_at.desc())\
                          .paginate(page=page, per_page=10)
    
    return render_template('cases/index.html', cases=cases)

@cases_bp.route('/cases/create', methods=['GET', 'POST'])
@login_required
def create_case():
    """Create a new case - with suspect autofill from profile"""
    case_form = CaseForm()
    suspect_form = SuspectForm()
    
    # Check if we have a suspect_id parameter (coming from suspect profile)
    prefill_suspect = None
    suspect_id = request.args.get('suspect_id', type=int)
    
    if suspect_id:
        prefill_suspect = Suspect.query.get(suspect_id)
        if prefill_suspect:
            # Prefill the suspect form with existing suspect data
            suspect_form.id_number.data = prefill_suspect.id_number
            suspect_form.first_name.data = prefill_suspect.first_name
            suspect_form.last_name.data = prefill_suspect.last_name
            suspect_form.date_of_birth.data = prefill_suspect.date_of_birth
            suspect_form.gender.data = prefill_suspect.gender
            suspect_form.address.data = prefill_suspect.address
            suspect_form.contact_number.data = prefill_suspect.contact_number
    
    if request.method == 'POST':
        # Check if we're using an existing suspect (from hidden field or form data)
        use_existing_suspect_id = request.form.get('use_existing_suspect', '').strip()
        
        print(f"POST received - use_existing_suspect: '{use_existing_suspect_id}'")
        print(f"Case form category: {request.form.get('category')}")
        print(f"Case form severity: {request.form.get('severity')}")
        
        # Manually validate and populate the form
        if case_form.validate_on_submit():
            suspect = None
            
            # Handle existing suspect
            if use_existing_suspect_id and use_existing_suspect_id.isdigit():
                suspect = Suspect.query.get(int(use_existing_suspect_id))
                if not suspect:
                    flash('Specified suspect not found.', 'danger')
                    return redirect(url_for('cases.create_case'))
                print(f"Using existing suspect ID: {suspect.id}")
            else:
                # Check if suspect exists by ID number
                id_number = suspect_form.id_number.data
                if id_number:
                    suspect = Suspect.query.filter_by(id_number=id_number).first()
                
                # If suspect doesn't exist, create new suspect
                if not suspect:
                    # Validate required fields for new suspect
                    if not suspect_form.first_name.data or not suspect_form.last_name.data:
                        flash('First name and last name are required for new suspects.', 'danger')
                        return redirect(url_for('cases.create_case'))
                    
                    # Parse date of birth
                    dob = None
                    if suspect_form.date_of_birth.data:
                        try:
                            if isinstance(suspect_form.date_of_birth.data, str):
                                dob = datetime.strptime(suspect_form.date_of_birth.data, '%Y-%m-%d').date()
                            else:
                                dob = suspect_form.date_of_birth.data
                        except:
                            dob = None
                    
                    suspect = Suspect(
                        id_number=suspect_form.id_number.data,
                        first_name=suspect_form.first_name.data,
                        last_name=suspect_form.last_name.data,
                        date_of_birth=dob,
                        gender=suspect_form.gender.data,
                        address=suspect_form.address.data,
                        contact_number=suspect_form.contact_number.data,
                        photo_path=None  # Will be set after photo upload
                    )
                    db.session.add(suspect)
                    db.session.flush()
                    print(f"Created new suspect ID: {suspect.id}")
                else:
                    print(f"Found existing suspect by ID number: {suspect.id}")
            
            # Parse incident date
            incident_date = None
            if case_form.incident_date.data:
                try:
                    # Try parsing datetime-local format (2026-01-21T12:59)
                    incident_date = datetime.strptime(case_form.incident_date.data, '%Y-%m-%dT%H:%M')
                except ValueError:
                    try:
                        # Try parsing date format (2026-01-21)
                        incident_date = datetime.strptime(case_form.incident_date.data, '%Y-%m-%d')
                    except ValueError:
                        incident_date = None
            
            # Create case
            case = Case(
                title=case_form.title.data,
                description=case_form.description.data,
                category=case_form.category.data,
                severity=case_form.severity.data,
                location=case_form.location.data,
                incident_date=incident_date,
                assigned_officer_id=current_user.id,
                suspect_id=suspect.id
            )
            case.generate_case_number()
            
            # Handle photo upload for new suspects
            if 'photo' in request.files and not use_existing_suspect_id:
                photo = request.files['photo']
                if photo.filename != '':
                    # Create upload directory if it doesn't exist
                    upload_dir = 'static/uploads/suspects'
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Generate secure filename
                    filename = secure_filename(f"suspect_{suspect.id}_{photo.filename}")
                    photo_path = os.path.join(upload_dir, filename)
                    
                    # Save the file
                    photo.save(photo_path)
                    
                    # Store relative path in database
                    suspect.photo_path = f'uploads/suspects/{filename}'
                    print(f"Saved photo: {photo_path}")
            
            # Add case to database
            db.session.add(case)
            db.session.flush()
            
            # Create case update record
            update = CaseUpdate(
                case_id=case.id,
                officer_id=current_user.id,
                update_type='case_created',
                notes=f'Case created by {current_user.full_name}'
            )
            db.session.add(update)
            
            db.session.commit()
            
            flash(f'Case {case.case_number} created successfully!', 'success')
            return redirect(url_for('cases.view_case', case_id=case.id))
        else:
            print(f"Case form validation errors: {case_form.errors}")
            if suspect_form.errors:
                print(f"Suspect form errors: {suspect_form.errors}")
            flash('Please correct the errors in the form.', 'danger')
    
    return render_template('cases/create.html', 
                         case_form=case_form, 
                         suspect_form=suspect_form,
                         prefill_suspect=prefill_suspect,
                         suspect_id=suspect_id)

@cases_bp.route('/cases/<int:case_id>')
@login_required
def view_case(case_id):
    """View a specific case"""
    case = Case.query.get_or_404(case_id)
    
    # Check access
    if not current_user.can_access_case(case):
        flash('You do not have permission to view this case.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('cases/view.html', case=case)

@cases_bp.route('/cases/<int:case_id>/update-status', methods=['POST'])
@login_required
def update_case_status(case_id):
    """Update case status"""
    case = Case.query.get_or_404(case_id)
    
    # Check permission
    if not case.can_be_modified_by(current_user):
        flash('You do not have permission to update this case.', 'danger')
        return redirect(url_for('cases.view_case', case_id=case_id))
    
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    
    if new_status and new_status in ['open', 'investigating', 'in_court', 'closed', 'archived']:
        # Create update record
        update = CaseUpdate(
            case_id=case.id,
            officer_id=current_user.id,
            update_type='status_change',
            previous_status=case.status,
            new_status=new_status,
            notes=notes
        )
        
        # Update case
        case.status = new_status
        case.updated_at = datetime.utcnow()
        
        db.session.add(update)
        db.session.commit()
        
        flash(f'Case status updated to {new_status}.', 'success')
    
    return redirect(url_for('cases.view_case', case_id=case_id))

@cases_bp.route('/api/check-suspect', methods=['POST'])
@login_required
def check_suspect():
    """Check if suspect already exists by ID number and return full details"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        id_number = data.get('id_number')
        
        if not id_number:
            return jsonify({'error': 'ID number is required'}), 400
        
        # Clean the ID number
        id_number = id_number.strip()
        
        suspect = Suspect.query.filter_by(id_number=id_number).first()
        
        if suspect:
            return jsonify({
                'exists': True,
                'suspect': {
                    'id': suspect.id,
                    'full_name': suspect.full_name,
                    'first_name': suspect.first_name,
                    'last_name': suspect.last_name,
                    'id_number': suspect.id_number,
                    'date_of_birth': suspect.date_of_birth.strftime('%Y-%m-%d') if suspect.date_of_birth else None,
                    'gender': suspect.gender,
                    'address': suspect.address,
                    'contact_number': suspect.contact_number,
                    'photo_path': suspect.photo_path,
                    'active_cases': suspect.active_cases
                }
            })
        
        return jsonify({'exists': False})
        
    except Exception as e:
        print(f"Error checking suspect: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@cases_bp.route('/api/get-suspect/<int:suspect_id>', methods=['GET'])
@login_required
def get_suspect(suspect_id):
    """Get suspect details by ID"""
    try:
        suspect = Suspect.query.get(suspect_id)
        
        if not suspect:
            return jsonify({'error': 'Suspect not found'}), 404
        
        return jsonify({
            'success': True,
            'suspect': {
                'id': suspect.id,
                'full_name': suspect.full_name,
                'first_name': suspect.first_name,
                'last_name': suspect.last_name,
                'id_number': suspect.id_number,
                'date_of_birth': suspect.date_of_birth.strftime('%Y-%m-%d') if suspect.date_of_birth else None,
                'gender': suspect.gender,
                'address': suspect.address,
                'contact_number': suspect.contact_number,
                'photo_path': suspect.photo_path,
                'active_cases': suspect.active_cases
            }
        })
        
    except Exception as e:
        print(f"Error getting suspect: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500