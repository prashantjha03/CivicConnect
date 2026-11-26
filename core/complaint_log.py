import json
from pathlib import Path

from django.conf import settings


def append_complaint_record(challenge):
    """Append a submitted complaint as one JSON document per line."""
    category = challenge.category
    record = {
        '_id': challenge.pk,
        'title': challenge.title,
        'description': challenge.description,
        'category': {
            'id': category.pk,
            'name': category.name,
        } if category else None,
        'department': {
            'id': challenge.department.pk,
            'name': challenge.department.name,
        } if challenge.department else None,
        'author': {
            'id': challenge.author.pk,
            'username': challenge.author.username,
        },
        'status': challenge.status,
        'location_name': challenge.location_name,
        'latitude': challenge.latitude,
        'longitude': challenge.longitude,
        'is_verified': challenge.is_verified,
        'created_at': challenge.created_at.isoformat(),
        'updated_at': challenge.updated_at.isoformat(),
        'images': list(challenge.images.values_list('image', flat=True)),
    }

    log_path = Path(settings.COMPLAINT_LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('a', encoding='utf-8') as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False))
        log_file.write('\n')
