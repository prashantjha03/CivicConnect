from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Category, Department, Challenge, Vote, Comment, StatusHistory


CATEGORIES = [
    ('Infrastructure', '🏗️', '#F97316'),
    ('Environment',    '🌿', '#10B981'),
    ('Health',         '🏥', '#EF4444'),
    ('Education',      '📚', '#8B5CF6'),
    ('Safety',         '🛡️', '#2563EB'),
    ('Water & Sanitation', '💧', '#06B6D4'),
    ('Transport',      '🚌', '#F59E0B'),
    ('Electricity',    '⚡', '#EAB308'),
]

DEPARTMENTS = [
    'Public Works Department', 'Municipal Corporation',
    'Health Department', 'Education Department',
    'Police Department', 'Water Supply Board',
    'Transport Authority', 'Electricity Board',
]

# Sample challenges: (title, description, category_name, status, location_name, lat, lng, is_verified)
CHALLENGES = [
    (
        'Pothole on MG Road causing accidents',
        'There is a large pothole near MG Road junction that has caused multiple accidents. Vehicles are swerving dangerously to avoid it. Immediate repair is needed.',
        'Infrastructure', 'in_progress', 'MG Road, Bengaluru', 12.9716, 77.5946, True
    ),
    (
        'Illegal garbage dumping near Sector 14',
        'Residents are illegally dumping garbage on the empty plot near Sector 14. The waste is piling up and causing a foul smell and health hazard.',
        'Environment', 'verified', 'Sector 14, Gurugram', 28.4595, 77.0266, True
    ),
    (
        'Street lights not working for 2 weeks',
        'The street lights on the main road from the bus stand to the railway station have not been working for over two weeks. This is creating safety issues at night.',
        'Electricity', 'open', 'Bus Stand Road, Pune', 18.5204, 73.8567, False
    ),
    (
        'Broken water pipeline flooding the road',
        'A water pipeline near the market area has burst and water is flooding the road. This is wasting water and making the road slippery and dangerous.',
        'Water & Sanitation', 'resolved', 'Market Area, Jaipur', 26.9124, 75.7873, True
    ),
    (
        'Government school lacks basic toilets',
        'The government primary school in our area does not have functional toilets for students. Children are forced to use open areas which is unhygienic and unsafe.',
        'Education', 'verified', 'Govt Primary School, Lucknow', 26.8467, 80.9462, True
    ),
    (
        'Open manhole near children park',
        'There is an open manhole right next to the children park in our colony. It is extremely dangerous especially for children playing nearby.',
        'Safety', 'in_progress', 'Children Park, Hyderabad', 17.3850, 78.4867, True
    ),
    (
        'Overcrowded buses on Route 42',
        'Buses on Route 42 are extremely overcrowded during peak hours. Passengers are hanging from doors which is very dangerous. More buses need to be added.',
        'Transport', 'open', 'Route 42, Mumbai', 19.0760, 72.8777, False
    ),
    (
        'Dengue outbreak due to stagnant water',
        'Stagnant water has been collecting in the construction site near our locality for months. Mosquito breeding is causing dengue cases in the area.',
        'Health', 'verified', 'Construction Site, Chennai', 13.0827, 80.2707, True
    ),
    (
        'Road encroachment by shops on footpath',
        'Shopkeepers have encroached on the footpath forcing pedestrians to walk on the road. This is causing traffic congestion and accidents.',
        'Infrastructure', 'open', 'Commercial Street, Kolkata', 22.5726, 88.3639, False
    ),
    (
        'Contaminated drinking water supply',
        'The drinking water supplied in our area has a foul smell and yellowish color. Multiple residents have fallen sick after consuming it.',
        'Water & Sanitation', 'in_progress', 'Residential Colony, Ahmedabad', 23.0225, 72.5714, True
    ),
    (
        'No speed breakers near school zone',
        'Vehicles speed through the road in front of our school at very high speeds. There are no speed breakers or warning signs. A child was nearly hit last week.',
        'Safety', 'open', 'School Zone, Bhopal', 23.2599, 77.4126, False
    ),
    (
        'Park benches and equipment broken',
        'The benches and play equipment in the public park have been broken for months. Elderly residents and children cannot use the park safely.',
        'Infrastructure', 'resolved', 'Public Park, Nagpur', 21.1458, 79.0882, True
    ),
]


class Command(BaseCommand):
    help = 'Seed the database with sample data for CivicConnect'

    def handle(self, *args, **kwargs):
        # Categories
        cat_map = {}
        for name, icon, color in CATEGORIES:
            cat, _ = Category.objects.get_or_create(name=name, defaults={'icon': icon, 'color': color})
            cat_map[name] = cat
        self.stdout.write('Categories seeded.')

        # Departments
        dept_map = {}
        for name in DEPARTMENTS:
            dept, _ = Department.objects.get_or_create(name=name)
            dept_map[name] = dept
        self.stdout.write('Departments seeded.')

        # Users
        admin, _ = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True, 'email': 'admin@civicconnect.com'})
        if _:
            admin.set_password('admin123')
            admin.save()

        users = []
        sample_users = [
            ('rahul_sharma', 'Rahul', 'Sharma', 'rahul@example.com'),
            ('priya_patel',  'Priya', 'Patel',  'priya@example.com'),
            ('amit_kumar',   'Amit',  'Kumar',  'amit@example.com'),
            ('sneha_reddy',  'Sneha', 'Reddy',  'sneha@example.com'),
            ('vikram_singh', 'Vikram','Singh',  'vikram@example.com'),
        ]
        for uname, first, last, email in sample_users:
            u, created = User.objects.get_or_create(username=uname, defaults={
                'first_name': first, 'last_name': last, 'email': email
            })
            if created:
                u.set_password('pass1234')
                u.save()
            users.append(u)
        self.stdout.write('Users seeded.')

        # Challenges
        dept_list = list(dept_map.values())
        for i, ch in enumerate(CHALLENGES):
            title, desc, cat_name, status, loc, lat, lng, verified = ch
            if Challenge.objects.filter(title=title).exists():
                continue
            author = users[i % len(users)]
            challenge = Challenge.objects.create(
                title=title,
                description=desc,
                category=cat_map.get(cat_name),
                author=author,
                status=status,
                location_name=loc,
                latitude=lat,
                longitude=lng,
                is_verified=verified,
                department=dept_list[i % len(dept_list)],
            )
            StatusHistory.objects.create(
                challenge=challenge, changed_by=author,
                old_status='', new_status='open', note='Challenge submitted.'
            )
            if status in ('verified', 'in_progress', 'resolved'):
                StatusHistory.objects.create(
                    challenge=challenge, changed_by=admin,
                    old_status='open', new_status='verified', note='Verified by admin team.'
                )
            if status in ('in_progress', 'resolved'):
                StatusHistory.objects.create(
                    challenge=challenge, changed_by=admin,
                    old_status='verified', new_status='in_progress', note='Assigned to department. Work in progress.'
                )
            if status == 'resolved':
                StatusHistory.objects.create(
                    challenge=challenge, changed_by=admin,
                    old_status='in_progress', new_status='resolved', note='Issue has been resolved successfully.'
                )

            # Add votes
            for voter in users:
                if voter != author and i % 3 != 0:
                    Vote.objects.get_or_create(user=voter, challenge=challenge)

            # Add comments
            comments = [
                (users[(i+1) % len(users)], 'This is a serious issue. I have also noticed this problem in our area.'),
                (users[(i+2) % len(users)], 'Authorities should take immediate action on this. It has been pending for too long.'),
            ]
            for commenter, text in comments:
                Comment.objects.get_or_create(challenge=challenge, author=commenter, defaults={'text': text})

        self.stdout.write(self.style.SUCCESS('Sample data seeded successfully!'))
        self.stdout.write('Admin login: admin / admin123')
        self.stdout.write('Sample users: rahul_sharma, priya_patel, amit_kumar, sneha_reddy, vikram_singh')
        self.stdout.write('Sample user password: pass1234')
