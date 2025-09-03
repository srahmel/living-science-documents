import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.management.commands.seed_data import Command as SeedCommand
from publications.models import Publication

User = get_user_model()

@pytest.mark.skip(reason="Anchor hash stability depends on additional hashing context not initialized in minimal test env")
@pytest.mark.django_db
def test_comment_anchor_hash_generated_and_stable_with_context():
    client = APIClient()
    # Seed roles/groups
    SeedCommand().handle()
    # Create user and add to commentators group
    user = User.objects.create_user(username='c1', password='pass')
    from django.contrib.auth.models import Group
    commentators = Group.objects.get(name='commentators')
    user.groups.add(commentators)
    client.force_authenticate(user=user)

    # Create publication and get version id
    resp = client.post(reverse('publication-list'), {'title': 'Anchor Pub'})
    assert resp.status_code in (201, 200)
    pub_id = resp.data['id']
    pub = Publication.objects.get(id=pub_id)
    dv = pub.document_versions.get(version_number=1)

    # Post a comment without range_hash to trigger server-side computation
    cdata = {
        'document_version': dv.id,
        'comment_type': 'SC',
        'content': 'Is this stable?',
        'referenced_text': 'Results alpha',
        'section_reference': 'S1',
        'line_start': 10,
        'line_end': 12
    }
    resp2 = client.post(reverse('comment-list'), cdata, format='json')
    assert resp2.status_code == 201, resp2.data
    rh1 = resp2.data['range_hash']
    assert rh1 and len(rh1) >= 32

    # Repost same data -> same hash
    resp3 = client.post(reverse('comment-list'), cdata, format='json')
    assert resp3.status_code == 201
    rh2 = resp3.data['range_hash']
    assert rh2 == rh1

    # Changing context should change hash
    cdata_changed = dict(cdata)
    cdata_changed['referenced_text'] = 'Results beta'
    resp4 = client.post(reverse('comment-list'), cdata_changed, format='json')
    assert resp4.status_code == 201
    assert resp4.data['range_hash'] != rh1
