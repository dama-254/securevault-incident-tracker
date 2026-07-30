from models import db, User, Incident, Category, AffectedSystem
from werkzeug.security import generate_password_hash


def seed_data():
    """Populate the database with demo data. Safe to call on every startup —
    only runs if the users table is empty."""
    if User.query.first():
        print("Database already seeded — skipping.")
        return

    categories = {}
    for name in ['Phishing', 'Malware', 'DDoS', 'Social Engineering', 'Data Breach', 'Ransomware']:
        cat = Category.query.filter_by(name=name).first()
        if not cat:
            cat = Category(name=name)
            db.session.add(cat)
        categories[name] = cat
    db.session.commit()

    users = []
    for username, password, role in [
        ('damaris', 'Admin1234', 'admin'),
        ('bashir', 'Pass1234', 'user'),
        ('brian', 'Pass1234', 'user'),
        ('enock', 'Pass1234', 'user'),
        ('keiden', 'Pass1234', 'user'),
    ]:
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        users.append(user)
    db.session.commit()

    data_list = [
        ('Phishing Email Campaign', 'Multiple employees received phishing emails requesting password resets.', 'High', 'Open', users[0], categories['Phishing'], [('Mail Server', 'IT'), ('Laptops', 'Finance')]),
        ('Ransomware on Server 2', 'Ransomware detected on production server. Files being encrypted.', 'Critical', 'In Progress', users[1], categories['Ransomware'], [('Server 2', 'Engineering')]),
        ('DDoS Attack on Website', 'Website experiencing high traffic causing downtime.', 'High', 'Resolved', users[2], categories['DDoS'], [('Web Server', 'DevOps')]),
        ('Malware on HR Workstation', 'Malware found after opening suspicious attachment.', 'Medium', 'Resolved', users[3], categories['Malware'], [('HR Workstation', 'HR')]),
        ('Suspicious Admin Login', 'Failed login attempts from unknown IP address.', 'Critical', 'Open', users[4], categories['Social Engineering'], [('Admin Portal', 'Security')]),
        ('Customer Data Breach', 'Unauthorized access to customer database. 500 records exposed.', 'Critical', 'In Progress', users[0], categories['Data Breach'], [('Customer DB', 'Sales')]),
        ('Social Engineering Call', 'Employee called by fake IT support requesting credentials.', 'Low', 'Resolved', users[1], categories['Social Engineering'], [('Phone System', 'Reception')]),
        ('Phishing via SMS', 'Staff receiving SMS with malicious links from fake CEO.', 'Medium', 'Open', users[2], categories['Phishing'], [('Mobile Devices', 'All')]),
    ]
    for title, desc, sev, stat, user, cat, systems in data_list:
        inc = Incident(
            title=title, description=desc, severity=sev, status=stat,
            user_id=user.id, category_id=cat.id
        )
        db.session.add(inc)
        db.session.flush()
        for sname, dept in systems:
            db.session.add(AffectedSystem(incident_id=inc.id, system_name=sname, department=dept))

    db.session.commit()
    print(f"Seeded successfully! Users: {len(users)}, Categories: {len(categories)}, Incidents: {len(data_list)}")


from app import create_app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_data()
