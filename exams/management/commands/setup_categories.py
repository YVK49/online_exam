from django.core.management.base import BaseCommand
from exams.models import ExamCategory
import json

class Command(BaseCommand):
    help = 'Set up exam categories with question counts'

    def handle(self, *args, **kwargs):
        categories = [
            {'name': 'JEE MAINS', 'question_count': {
                'Physics': {'MCQ_SINGLE': 20, 'NUMERICAL': 5},
                'Chemistry': {'MCQ_SINGLE': 20, 'NUMERICAL': 5},
                'Maths': {'MCQ_SINGLE': 20, 'NUMERICAL': 5}
            }},
            {'name': 'JEE ADVANCED', 'question_count': {
                'Physics': {'MCQ_SINGLE': 4, 'MCQ_MULTI': 3, 'NUMERICAL': 6},
                'Chemistry': {'MCQ_SINGLE': 4, 'MCQ_MULTI': 3, 'NUMERICAL': 6},
                'Maths': {'MCQ_SINGLE': 4, 'MCQ_MULTI': 3, 'NUMERICAL': 6}
            }},
            {'name': 'EAMCET', 'question_count': {}, 'subcategories': [
                {'name': 'EAMCET MPC', 'question_count': {
                    'Maths': {'MCQ_SINGLE': 80},
                    'Physics': {'MCQ_SINGLE': 40},
                    'Chemistry': {'MCQ_SINGLE': 40}
                }},
                {'name': 'EAMCET BiPC', 'question_count': {
                    'Botany': {'MCQ_SINGLE': 40},
                    'Zoology': {'MCQ_SINGLE': 40},
                    'Physics': {'MCQ_SINGLE': 40},
                    'Chemistry': {'MCQ_SINGLE': 40}
                }},
            ]},
            {'name': 'NEET', 'question_count': {
                'Physics': {'MCQ_SINGLE': 50},
                'Chemistry': {'MCQ_SINGLE': 50},
                'Biology': {'MCQ_SINGLE': 100}
            }},
        ]

        for cat in categories:
            parent, created = ExamCategory.objects.get_or_create(
                name=cat['name'],
                defaults={'question_count': json.dumps(cat['question_count'])}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat["name"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {cat["name"]}'))

            if 'subcategories' in cat:
                for subcat in cat['subcategories']:
                    subcat_obj, subcat_created = ExamCategory.objects.get_or_create(
                        name=subcat['name'],
                        parent=parent,
                        defaults={'question_count': json.dumps(subcat['question_count'])}
                    )
                    if subcat_created:
                        self.stdout.write(self.style.SUCCESS(f'Created subcategory: {subcat["name"]}'))
                    else:
                        self.stdout.write(self.style.WARNING(f'Subcategory already exists: {subcat["name"]}'))