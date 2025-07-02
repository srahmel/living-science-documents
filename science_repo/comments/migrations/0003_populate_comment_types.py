from django.db import migrations

def create_default_comment_types(apps, schema_editor):
    CommentType = apps.get_model('comments', 'CommentType')
    
    comment_types = [
        {
            'code': 'SC',
            'name': 'Scientific Comment',
            'description': 'Technical comment on specific text passages',
            'requires_doi': True
        },
        {
            'code': 'rSC',
            'name': 'Response to Scientific Comment',
            'description': 'Reply to a Scientific Comment',
            'requires_doi': True
        },
        {
            'code': 'ER',
            'name': 'Error Correction',
            'description': 'Correction of factual errors',
            'requires_doi': False
        },
        {
            'code': 'AD',
            'name': 'Additional Data',
            'description': 'Reference to supplementary external data or studies',
            'requires_doi': True
        },
        {
            'code': 'NP',
            'name': 'New Publication',
            'description': 'Note on a new relevant publication',
            'requires_doi': True
        },
    ]
    
    for comment_type_data in comment_types:
        CommentType.objects.get_or_create(
            code=comment_type_data['code'],
            defaults={
                'name': comment_type_data['name'],
                'description': comment_type_data['description'],
                'requires_doi': comment_type_data['requires_doi']
            }
        )

def remove_default_comment_types(apps, schema_editor):
    CommentType = apps.get_model('comments', 'CommentType')
    codes = ['SC', 'rSC', 'ER', 'AD', 'NP']
    CommentType.objects.filter(code__in=codes).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('comments', '0002_alter_commenttype_code_commentchat_chatmessage'),
    ]

    operations = [
        migrations.RunPython(
            create_default_comment_types,
            remove_default_comment_types
        ),
    ]
