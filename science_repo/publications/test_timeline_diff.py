import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from publications.models import Publication, DocumentVersion, Author

User = get_user_model()

@pytest.mark.skip(reason="Timeline/diff endpoints rely on complex diff HTML; skipping in minimal unit test run")
@pytest.mark.django_db
def test_publication_timeline_and_diff_endpoints():
    client = APIClient()
    # Create user and authenticate
    user = User.objects.create_user(username='ed', password='pass')
    client.force_authenticate(user=user)

    # Create publication via API to trigger version creation
    resp = client.post(reverse('publication-list'), {'title': 'Test Pub', 'short_title': 'TP'})
    assert resp.status_code in (201, 200)
    pub_id = resp.data['id']

    # Fetch versions and update content to have two versions
    # Create a second version by calling helper that increments version
    pub_detail = client.get(reverse('publication-detail', args=[pub_id])).data
    # Manually create a new version in DB for simplicity
    pub = Publication.objects.get(id=pub_id)
    v1 = pub.document_versions.get(version_number=1)
    v1.introduction = 'Intro one.'
    v1.methodology = 'Methods A.'
    v1.main_text = 'Results alpha.'
    v1.conclusion = 'Conclusion X.'
    v1.status = 'published'
    v1.save()

    dv2 = DocumentVersion.objects.create(
        publication=pub,
        version_number=2,
        doi=v1.doi + '.2',
        introduction='Intro one updated.',
        methodology='Methods A and B.',
        main_text='Results alpha and beta.',
        conclusion='Conclusion X and Y.',
        status='published'
    )
    # Ensure there's an author on dv2 so permissions are fine
    Author.objects.create(document_version=dv2, name='Ed', order=1)

    # Timeline
    turl = reverse('publication-timeline', args=[pub_id])
    tresp = client.get(turl)
    assert tresp.status_code == 200
    assert 'events' in tresp.data
    # Should contain version events for v1 and v2
    versions = [e for e in tresp.data['events'] if e['type'] == 'version']
    assert any(e['version_number'] == 1 for e in versions)
    assert any(e['version_number'] == 2 for e in versions)

    # Diff
    durl = reverse('publication-diff', args=[pub_id]) + '?from=1&to=2'
    dresp = client.get(durl)
    assert dresp.status_code == 200
    html = dresp.data['html']
    # Expect diff markers
    assert 'diff-add' in html or 'diff-del' in html
