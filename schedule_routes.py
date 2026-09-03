from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import models
from datetime import datetime, date, timedelta

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('/volunteers')
def volunteers():
    conn = models.get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM volunteers ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return render_template('volunteers.html', volunteers=rows)


@schedule_bp.route('/volunteers/add', methods=['POST'])
def add_volunteer():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    is_manager = 1 if request.form.get('is_manager') == 'on' else 0

    if not name or not email:
        flash('Name and email required', 'error')
        return redirect(url_for('schedule.volunteers'))

    conn = models.get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO volunteers (name, email, phone, is_manager) VALUES (?, ?, ?, ?)", (name, email, phone, is_manager))
        conn.commit()
        flash('Volunteer added', 'success')
    except Exception as e:
        flash('Could not add volunteer: ' + str(e), 'error')
    finally:
        conn.close()

    return redirect(url_for('schedule.volunteers'))


@schedule_bp.route('/volunteers/delete/<int:vid>')
def delete_volunteer(vid):
    conn = models.get_db()
    c = conn.cursor()
    c.execute("DELETE FROM volunteers WHERE id = ?", (vid,))
    conn.commit()
    conn.close()
    flash('Volunteer removed', 'success')
    return redirect(url_for('schedule.volunteers'))


@schedule_bp.route('/shifts')
def shifts():
    conn = models.get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM shifts ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()
    return render_template('shifts.html', shifts=rows)


@schedule_bp.route('/shifts/add', methods=['POST'])
def add_shift():
    date_str = request.form.get('date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    description = request.form.get('description', '')

    conn = models.get_db()
    c = conn.cursor()
    c.execute("INSERT INTO shifts (date, start_time, end_time, description) VALUES (?, ?, ?, ?)", (date_str, start_time, end_time, description))
    conn.commit()
    conn.close()
    flash('Shift created', 'success')
    return redirect(url_for('schedule.shifts'))


@schedule_bp.route('/assign', methods=['POST'])
def assign():
    shift_id = int(request.form.get('shift_id'))
    volunteer_id = int(request.form.get('volunteer_id'))
    conn = models.get_db()
    c = conn.cursor()
    c.execute("INSERT INTO assignments (shift_id, volunteer_id) VALUES (?, ?)", (shift_id, volunteer_id))
    conn.commit()
    conn.close()
    flash('Volunteer assigned to shift', 'success')
    return redirect(url_for('schedule.shifts'))


@schedule_bp.route('/bag_count', methods=['POST'])
def bag_count():
    shift_id = int(request.form.get('shift_id'))
    volunteer_id = int(request.form.get('volunteer_id'))
    bags = int(request.form.get('bags'))
    conn = models.get_db()
    c = conn.cursor()
    c.execute("INSERT INTO bag_counts (shift_id, volunteer_id, bags, recorded_at) VALUES (?, ?, ?, ?)", (shift_id, volunteer_id, bags, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    flash('Bag count recorded', 'success')
    return redirect(url_for('schedule.shifts'))


@schedule_bp.route('/reports')
def reports():
    period = request.args.get('period', 'weekly')
    conn = models.get_db()
    c = conn.cursor()

    today = date.today()
    if period == 'weekly':
        start = today - timedelta(days=today.weekday())
    elif period == 'monthly':
        start = today.replace(day=1)
    elif period == 'yearly':
        start = date(today.year, 1, 1)
    else:
        start = today - timedelta(days=7)

    c.execute("SELECT SUM(bags) as total_bags FROM bag_counts WHERE recorded_at >= ?", (start.isoformat(),))
    total = c.fetchone()
    total_bags = total['total_bags'] if total and total['total_bags'] is not None else 0

    # Simple assignments count
    c.execute("SELECT COUNT(*) as assigned FROM assignments")
    assigned = c.fetchone()['assigned']
    conn.close()
    return render_template('reports.html', period=period, total_bags=total_bags, assigned=assigned)
