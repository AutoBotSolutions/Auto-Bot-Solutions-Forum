"""
Advanced User Role Management Routes

This module contains routes for advanced user role management including:
- Role creation and management
- Permission management
- Role assignment workflows
- Role hierarchy management
- Role analytics
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models import User
from app.admin.roles.models import (
    Role, Permission, RolePermission, UserRole, RoleAssignment, 
    RoleWorkflow, RoleAnalytics, RoleHierarchy
)
from app.admin.roles.forms import (
    RoleForm, PermissionForm, RolePermissionForm, AssignRoleForm, RemoveRoleForm,
    RoleRequestForm, RoleApprovalForm, RoleWorkflowForm, RoleHierarchyForm,
    UserSearchForm, RoleAnalyticsForm, BulkRoleAssignmentForm, BulkRoleRemovalForm,
    RoleTemplateForm, RoleImportForm, RoleExportForm, RoleSettingsForm,
    RoleAuditForm, PermissionCheckForm, RoleComparisonForm
)
import json
import csv
import io
from datetime import datetime, timedelta

roles_bp = Blueprint('roles', __name__, url_prefix='/admin/roles')

# Role Management

@roles_bp.route('/')
@login_required
def role_list():
    """List all roles"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    roles = Role.query.all()
    
    # Calculate user counts for each role
    for role in roles:
        role.user_count = role.get_user_count()
    
    return render_template('admin/roles/role_list.html', roles=roles)

@roles_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_role():
    """Create a new role"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = RoleForm()
    
    if form.validate_on_submit():
        role = Role.create_role(
            name=form.name.data,
            display_name=form.display_name.data,
            description=form.description.data,
            color=form.color.data or '#007bff',
            icon=form.icon.data,
            level=form.level.data or 0,
            is_admin_role=form.is_admin_role.data
        )
        
        flash(f'Role "{role.display_name}" created successfully.', 'success')
        return redirect(url_for('roles.role_list'))
    
    return render_template('admin/roles/create_role.html', form=form)

@roles_bp.route('/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    """Edit a role"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    role = Role.query.get_or_404(role_id)
    form = RoleForm()
    
    if form.validate_on_submit():
        role.name = form.name.data
        role.display_name = form.display_name.data
        role.description = form.description.data
        role.color = form.color.data or '#007bff'
        role.icon = form.icon.data
        role.level = form.level.data or 0
        role.is_active = form.is_active.data
        role.is_admin_role = form.is_admin_role.data
        role.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'Role "{role.display_name}" updated successfully.', 'success')
        return redirect(url_for('roles.role_list'))
    
    # Pre-fill form
    form.name.data = role.name
    form.display_name.data = role.display_name
    form.description.data = role.description
    form.color.data = role.color
    form.icon.data = role.icon
    form.level.data = role.level
    form.is_active.data = role.is_active
    form.is_admin_role.data = role.is_admin_role
    
    return render_template('admin/roles/edit_role.html', form=form, role=role)

@roles_bp.route('/<int:role_id>/delete', methods=['POST'])
@login_required
def delete_role(role_id):
    """Delete a role"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    role = Role.query.get_or_404(role_id)
    
    if role.is_system_role:
        flash('Cannot delete system roles.', 'error')
        return redirect(url_for('roles.role_list'))
    
    if role.get_user_count() > 0:
        flash('Cannot delete role with assigned users.', 'error')
        return redirect(url_for('roles.role_list'))
    
    db.session.delete(role)
    db.session.commit()
    
    flash(f'Role "{role.display_name}" deleted successfully.', 'success')
    return redirect(url_for('roles.role_list'))

# Permission Management

@roles_bp.route('/permissions')
@login_required
def permission_list():
    """List all permissions"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    permissions = Permission.query.all()
    return render_template('admin/roles/permission_list.html', permissions=permissions)

@roles_bp.route('/permissions/create', methods=['GET', 'POST'])
@login_required
def create_permission():
    """Create a new permission"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = PermissionForm()
    
    if form.validate_on_submit():
        permission = Permission.create_permission(
            name=form.name.data,
            display_name=form.display_name.data,
            description=form.description.data,
            category=form.category.data,
            resource=form.resource.data,
            action=form.action.data
        )
        
        flash(f'Permission "{permission.display_name}" created successfully.', 'success')
        return redirect(url_for('roles.permission_list'))
    
    return render_template('admin/roles/create_permission.html', form=form)

@roles_bp.route('/<int:role_id>/permissions')
@login_required
def role_permissions(role_id):
    """Manage role permissions"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    role = Role.query.get_or_404(role_id)
    all_permissions = Permission.query.filter_by(is_active=True).all()
    
    # Get current role permissions
    role_permission_ids = [rp.permission_id for rp in role.role_permissions]
    
    return render_template('admin/roles/role_permissions.html',
                         role=role,
                         all_permissions=all_permissions,
                         role_permission_ids=role_permission_ids)

@roles_bp.route('/<int:role_id>/permissions/update', methods=['POST'])
@login_required
def update_role_permissions(role_id):
    """Update role permissions"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    role = Role.query.get_or_404(role_id)
    permission_ids = request.form.getlist('permissions')
    
    # Remove existing permissions
    RolePermission.query.filter_by(role_id=role_id).delete()
    
    # Add new permissions
    for permission_id in permission_ids:
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=int(permission_id),
            granted=True,
            granted_by_id=current_user.id
        )
        db.session.add(role_permission)
    
    db.session.commit()
    flash(f'Permissions for role "{role.display_name}" updated successfully.', 'success')
    return redirect(url_for('roles.role_permissions', role_id=role_id))

# Role Assignment

@roles_bp.route('/assignments')
@login_required
def role_assignments():
    """Manage role assignments"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    assignments = UserRole.query.filter_by(is_active=True).all()
    return render_template('admin/roles/role_assignments.html', assignments=assignments)

@roles_bp.route('/assignments/assign', methods=['GET', 'POST'])
@login_required
def assign_role():
    """Assign role to user"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = AssignRoleForm()
    
    # Populate form choices
    form.user_id.choices = [(u.id, u.username) for u in User.query.filter_by(is_active=True).all()]
    form.role_id.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        assignment = UserRole.assign_role(
            user_id=form.user_id.data,
            role_id=form.role_id.data,
            assigned_by_id=current_user.id,
            expires_at=form.expires_at.data
        )
        
        user = User.query.get(form.user_id.data)
        role = Role.query.get(form.role_id.data)
        
        # Create assignment record
        RoleAssignment.create_request(
            user_id=form.user_id.data,
            role_id=form.role_id.data,
            requested_by_id=current_user.id,
            reason=form.reason.data
        )
        
        flash(f'Role "{role.display_name}" assigned to {user.username}.', 'success')
        return redirect(url_for('roles.role_assignments'))
    
    return render_template('admin/roles/assign_role.html', form=form)

@roles_bp.route('/assignments/remove', methods=['GET', 'POST'])
@login_required
def remove_role():
    """Remove role from user"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = RemoveRoleForm()
    
    # Populate form choices
    form.user_id.choices = [(u.id, u.username) for u in User.query.filter_by(is_active=True).all()]
    form.role_id.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        if UserRole.remove_role(form.user_id.data, form.role_id.data):
            user = User.query.get(form.user_id.data)
            role = Role.query.get(form.role_id.data)
            
            # Create removal record
            RoleAssignment.create_request(
                user_id=form.user_id.data,
                role_id=form.role_id.data,
                requested_by_id=current_user.id,
                reason=form.reason.data
            )
            
            flash(f'Role "{role.display_name}" removed from {user.username}.', 'success')
        else:
            flash('Unable to remove role.', 'error')
        
        return redirect(url_for('roles.role_assignments'))
    
    return render_template('admin/roles/remove_role.html', form=form)

# Role Requests

@roles_bp.route('/requests')
@login_required
def role_requests():
    """Manage role requests"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    requests = RoleAssignment.query.filter_by(workflow_type='request').order_by(
        RoleAssignment.created_at.desc()
    ).all()
    
    return render_template('admin/roles/role_requests.html', requests=requests)

@roles_bp.route('/requests/<int:request_id>/process', methods=['GET', 'POST'])
@login_required
def process_role_request(request_id):
    """Process a role request"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    request_obj = RoleAssignment.query.get_or_404(request_id)
    form = RoleApprovalForm()
    form.request_id.data = request_id
    
    if form.validate_on_submit():
        if form.action.data == 'approve':
            success = request_obj.approve(current_user.id)
            if success:
                flash('Role request approved.', 'success')
            else:
                flash('Unable to approve request.', 'error')
        else:
            success = request_obj.reject(current_user.id, form.reason.data)
            if success:
                flash('Role request rejected.', 'success')
            else:
                flash('Unable to reject request.', 'error')
        
        return redirect(url_for('roles.role_requests'))
    
    return render_template('admin/roles/process_request.html', form=form, request_obj=request_obj)

# Role Workflows

@roles_bp.route('/workflows')
@login_required
def role_workflows():
    """Manage role workflows"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    workflows = RoleWorkflow.query.all()
    return render_template('admin/roles/role_workflows.html', workflows=workflows)

@roles_bp.route('/workflows/create', methods=['GET', 'POST'])
@login_required
def create_workflow():
    """Create a new role workflow"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = RoleWorkflowForm()
    
    # Populate role choices
    form.role_id.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    form.approval_roles.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        approval_roles = form.approval_roles.data if form.requires_approval.data else []
        
        conditions = {}
        if form.min_registration_days.data:
            conditions['min_registration_days'] = form.min_registration_days.data
        if form.min_posts.data:
            conditions['min_posts'] = form.min_posts.data
        if form.require_active_account.data:
            conditions['require_active_account'] = True
        if form.require_verified_email.data:
            conditions['require_verified_email'] = True
        
        workflow = RoleWorkflow.create_workflow(
            name=form.name.data,
            description=form.description.data,
            role_id=form.role_id.data,
            workflow_type=form.workflow_type.data,
            requires_approval=form.requires_approval.data,
            approval_roles=approval_roles,
            auto_assign=form.auto_assign.data,
            conditions=conditions
        )
        
        flash(f'Workflow "{workflow.name}" created successfully.', 'success')
        return redirect(url_for('roles.role_workflows'))
    
    return render_template('admin/roles/create_workflow.html', form=form)

# Role Hierarchy

@roles_bp.route('/hierarchy')
@login_required
def role_hierarchy():
    """Manage role hierarchy"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    hierarchies = RoleHierarchy.query.all()
    roles = Role.query.filter_by(is_active=True).all()
    
    return render_template('admin/roles/role_hierarchy.html', hierarchies=hierarchies, roles=roles)

@roles_bp.route('/hierarchy/create', methods=['POST'])
@login_required
def create_hierarchy():
    """Create role hierarchy relationship"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = RoleHierarchyForm()
    
    # Populate role choices
    form.parent_role_id.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    form.child_role_id.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        hierarchy = RoleHierarchy.create_hierarchy(
            parent_role_id=form.parent_role_id.data,
            child_role_id=form.child_role_id.data,
            relationship_type=form.relationship_type.data
        )
        
        flash('Role hierarchy created successfully.', 'success')
        return redirect(url_for('roles.role_hierarchy'))
    
    return render_template('admin/roles/create_hierarchy.html', form=form)

# Role Analytics

@roles_bp.route('/analytics')
@login_required
def role_analytics():
    """Role analytics dashboard"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = RoleAnalyticsForm()
    
    # Populate role choices
    form.role_id.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    
    analytics_data = {}
    
    if request.args.get('role_id'):
        role_id = int(request.args.get('role_id'))
        days = int(request.args.get('date_range', 30))
        
        # Get role analytics
        analytics = RoleAnalytics.get_role_trends(role_id, days=days)
        analytics_data['trends'] = analytics
        
        # Get current role stats
        role = Role.query.get(role_id)
        analytics_data['current_stats'] = {
            'user_count': role.get_user_count(),
            'level': role.level,
            'is_admin': role.is_admin_role
        }
    
    return render_template('admin/roles/role_analytics.html',
                         form=form,
                         analytics_data=analytics_data)

@roles_bp.route('/analytics/calculate', methods=['POST'])
@login_required
def calculate_analytics():
    """Calculate role analytics"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    role_id = int(request.form.get('role_id'))
    
    # Calculate analytics for today
    analytics = RoleAnalytics.calculate_daily_analytics(role_id)
    
    flash('Analytics calculated successfully.', 'success')
    return redirect(url_for('roles.role_analytics', role_id=role_id))

# User Role Management

@roles_bp.route('/users/<int:user_id>/roles')
@login_required
def user_roles(user_id):
    """View user's roles"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    user_roles = UserRole.get_user_roles(user_id)
    available_roles = Role.query.filter_by(is_active=True).all()
    
    return render_template('admin/roles/user_roles.html',
                         user=user,
                         user_roles=user_roles,
                         available_roles=available_roles)

# Permission Checking

@roles_bp.route('/check-permission', methods=['GET', 'POST'])
@login_required
def check_permission():
    """Check user permissions"""
    form = PermissionCheckForm()
    
    # Populate user choices
    form.user_id.choices = [(u.id, u.username) for u in User.query.filter_by(is_active=True).all()]
    
    result = None
    
    if form.validate_on_submit():
        user = User.query.get(form.user_id.data)
        permission = form.permission.data
        
        # Check if user has permission
        user_roles = UserRole.get_user_roles(user_id=form.user_id.data)
        has_permission = False
        
        for user_role in user_roles:
            if user_role.role.has_permission(permission):
                has_permission = True
                break
        
        result = {
            'user': user.username,
            'permission': permission,
            'has_permission': has_permission
        }
    
    return render_template('admin/roles/check_permission.html', form=form, result=result)

# Bulk Operations

@roles_bp.route('/bulk-assign', methods=['GET', 'POST'])
@login_required
def bulk_assign_roles():
    """Bulk assign roles"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = BulkRoleAssignmentForm()
    
    # Populate role choices
    form.role_id.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        user_ids = json.loads(form.user_ids.data)
        
        for user_id in user_ids:
            UserRole.assign_role(
                user_id=user_id,
                role_id=form.role_id.data,
                assigned_by_id=current_user.id,
                expires_at=form.expires_at.data
            )
        
        flash(f'Role assigned to {len(user_ids)} users.', 'success')
        return redirect(url_for('roles.role_assignments'))
    
    return render_template('admin/roles/bulk_assign.html', form=form)

@roles_bp.route('/bulk-remove', methods=['GET', 'POST'])
@login_required
def bulk_remove_roles():
    """Bulk remove roles"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = BulkRoleRemovalForm()
    
    # Populate role choices
    form.role_id.choices = [(r.id, r.display_name) for r in Role.query.filter_by(is_active=True).all()]
    
    if form.validate_on_submit():
        user_ids = json.loads(form.user_ids.data)
        
        for user_id in user_ids:
            UserRole.remove_role(user_id, form.role_id.data)
        
        flash(f'Role removed from {len(user_ids)} users.', 'success')
        return redirect(url_for('roles.role_assignments'))
    
    return render_template('admin/roles/bulk_remove.html', form=form)

# Export/Import

@roles_bp.route('/export', methods=['GET', 'POST'])
@login_required
def export_roles():
    """Export roles data"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    form = RoleExportForm()
    
    if form.validate_on_submit():
        export_format = form.export_format.data
        
        # Get roles data
        roles = Role.query.all()
        data = []
        
        for role in roles:
            role_data = {
                'id': role.id,
                'name': role.name,
                'display_name': role.display_name,
                'description': role.description,
                'color': role.color,
                'icon': role.icon,
                'level': role.level,
                'is_active': role.is_active,
                'is_admin_role': role.is_admin_role,
                'permissions': role.permissions
            }
            
            if form.include_permissions.data:
                role_data['role_permissions'] = [
                    {
                        'permission_name': rp.permission.name,
                        'permission_display_name': rp.permission.display_name,
                        'granted': rp.granted
                    }
                    for rp in role.role_permissions
                ]
            
            if form.include_users.data:
                role_data['users'] = [
                    {
                        'user_id': ur.user.id,
                        'username': ur.user.username,
                        'assigned_at': ur.assigned_at.isoformat() if ur.assigned_at else None,
                        'expires_at': ur.expires_at.isoformat() if ur.expires_at else None
                    }
                    for ur in role.users
                ]
            
            data.append(role_data)
        
        if export_format == 'json':
            return send_file(
                io.BytesIO(json.dumps(data, indent=2).encode('utf-8')),
                mimetype='application/json',
                as_attachment=True,
                download_name='roles_export.json'
            )
        elif export_format == 'csv':
            # Simplified CSV export
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name='roles_export.csv'
            )
        
        flash('Export format not implemented.', 'info')
        return redirect(url_for('roles.export_roles'))
    
    return render_template('admin/roles/export_roles.html', form=form)

# API Endpoints

@roles_bp.route('/api/roles')
@login_required
def api_roles():
    """API endpoint for roles"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    roles = Role.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': role.id,
        'name': role.name,
        'display_name': role.display_name,
        'level': role.level,
        'user_count': role.get_user_count()
    } for role in roles])

@roles_bp.route('/api/users/<int:user_id>/permissions')
@login_required
def api_user_permissions(user_id):
    """API endpoint for user permissions"""
    if not current_user.is_admin and current_user.id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    user_roles = UserRole.get_user_roles(user_id)
    
    permissions = set()
    for user_role in user_roles:
        if user_role.role.permissions:
            permissions.update([p for p, granted in user_role.role.permissions.items() if granted])
    
    return jsonify(list(permissions))
