import json
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category


class ComplaintLogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='citizen', password='test-password')
        self.category = Category.objects.create(name='Roads')
        self.client.force_login(self.user)

    def test_submitted_complaints_are_appended_as_json_lines(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / 'complaints.jsonl'
            with override_settings(COMPLAINT_LOG_FILE=log_path):
                for title in ('Pothole on Main Street', 'Broken streetlight'):
                    response = self.client.post(reverse('submit_challenge'), {
                        'title': title,
                        'description': 'Please repair this issue.',
                        'category': str(self.category.pk),
                        'location_name': 'Main Street',
                    })
                    self.assertEqual(response.status_code, 302)

                records = [
                    json.loads(line)
                    for line in log_path.read_text(encoding='utf-8').splitlines()
                ]

        self.assertEqual(len(records), 2)
        self.assertEqual([record['title'] for record in records], [
            'Pothole on Main Street',
            'Broken streetlight',
        ])
        self.assertEqual(records[0]['category']['name'], 'Roads')
        self.assertEqual(records[0]['author']['username'], 'citizen')
        self.assertEqual(records[0]['status'], 'open')
