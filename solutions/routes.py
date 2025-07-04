from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Solution, StatusEnum
from extensions import db

solutions_bp = Blueprint('solutions', __name__, template_folder='templates')

@solutions_bp.route('/solution/<int:solution_id>')
@login_required
def view_solution(solution_id):
    """View solution details"""
    solution = Solution.query.get_or_404(solution_id)
    user = current_user
    
    return render_template('solution_detail.html', 
                         solution=solution, 
                         user=user)

@solutions_bp.route('/api/solutions', methods=['POST'])
@login_required
def create_solution_api():
    """Create a new solution from AI suggestions"""
    user = current_user
    
    # Validate manager+ permissions
    if not user or user.role.value not in ['Manager', 'Director', 'CEO', 'Admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    data = request.get_json()
    
    try:
        solution = Solution(
            problem_id=data['problem_id'],
            name=data['title'],  # Database requires name field
            title=data['title'], # Keep title for model consistency
            description=data['description'],
            status=StatusEnum.Open,
            created_by=user.id
        )
        
        db.session.add(solution)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': solution.id,
            'message': 'Solution created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500