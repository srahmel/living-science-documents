from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import Group
import random
import uuid
from datetime import timedelta

from core.models import User, CommentType as CoreCommentType
from publications.models import Publication, DocumentVersion, Author, Keyword
from comments.models import CommentType, Comment, CommentAuthor, CommentReference, ConflictOfInterest, CommentModeration

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with sample data based on the guidelines in .junie/guidelines.md'

    def add_arguments(self, parser):
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove all seeded data',
        )

    def handle(self, *args, **options):
        if options['remove']:
            self.remove_data()
        else:
            self.seed_data()

    def remove_data(self):
        """Remove all seeded data"""
        with transaction.atomic():
            # Mark users to be deleted with a special field
            self.stdout.write('Removing seeded users...')
            User.objects.filter(username__startswith='seed_').delete()

            # Remove seeded publications
            self.stdout.write('Removing seeded publications...')
            Publication.objects.filter(meta_doi__startswith='10.seed/').delete()

            # Remove seeded comment types if they were created
            self.stdout.write('Removing seeded comment types...')
            CommentType.objects.filter(code__in=['SC', 'rSC', 'ER', 'AD', 'NP']).delete()

            self.stdout.write(self.style.SUCCESS('Successfully removed all seeded data'))

    def seed_data(self):
        """Seed the database with sample data"""
        with transaction.atomic():
            # Ensure role groups exist
            self.create_groups()
            # Create comment types if they don't exist
            self.create_comment_types()

            # Create users with different roles
            users = self.create_users()
            self.assign_roles(users)

            # Create publications with document versions
            publications = self.create_publications(users)

            # Create comments on document versions
            self.create_comments(users, publications)

            self.stdout.write(self.style.SUCCESS('Successfully seeded database with sample data'))

    def create_groups(self):
        self.stdout.write('Ensuring role groups exist...')
        for name in [
            'readers', 'commentators', 'authors', 'moderators', 'review_editors', 'editorial_office', 'admins'
        ]:
            Group.objects.get_or_create(name=name)

    def create_comment_types(self):
        """Create comment types based on the guidelines"""
        self.stdout.write('Creating comment types...')

        comment_types = [
            {
                'code': 'SC',
                'name': 'Scientific Comment',
                'description': 'Fachlich-inhaltlicher Kommentar zu konkreten Textstellen',
                'requires_doi': True
            },
            {
                'code': 'rSC',
                'name': 'Response to Scientific Comment',
                'description': 'Erwiderung auf einen SC',
                'requires_doi': True
            },
            {
                'code': 'ER',
                'name': 'Error Correction',
                'description': 'Korrektur sachlicher Fehler',
                'requires_doi': False
            },
            {
                'code': 'AD',
                'name': 'Additional Data',
                'description': 'Verweis auf ergänzende externe Daten oder Studien',
                'requires_doi': True
            },
            {
                'code': 'NP',
                'name': 'New Publication',
                'description': 'Hinweis auf eine neue relevante Publikation',
                'requires_doi': True
            }
        ]

        for ct_data in comment_types:
            CommentType.objects.get_or_create(
                code=ct_data['code'],
                defaults={
                    'name': ct_data['name'],
                    'description': ct_data['description'],
                    'requires_doi': ct_data['requires_doi']
                }
            )

    def create_users(self):
        """Create users with different roles"""
        self.stdout.write('Creating users...')

        # Define user roles and data
        user_data = [
            # Authors
            {
                'username': 'seed_author1',
                'email': 'author1@example.com',
                'first_name': 'Anna',
                'last_name': 'Schmidt',
                'orcid': '0000-0001-1234-5678',
                'affiliation': 'Universität Berlin',
                'research_field': 'Molekularbiologie',
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'seed_author2',
                'email': 'author2@example.com',
                'first_name': 'Thomas',
                'last_name': 'Müller',
                'orcid': '0000-0002-2345-6789',
                'affiliation': 'Max-Planck-Institut',
                'research_field': 'Genetik',
                'is_staff': False,
                'is_superuser': False
            },
            # Commentators
            {
                'username': 'seed_commentator1',
                'email': 'commentator1@example.com',
                'first_name': 'Maria',
                'last_name': 'Weber',
                'orcid': '0000-0003-3456-7890',
                'affiliation': 'Universität München',
                'research_field': 'Biochemie',
                'is_staff': False,
                'is_superuser': False
            },
            {
                'username': 'seed_commentator2',
                'email': 'commentator2@example.com',
                'first_name': 'Stefan',
                'last_name': 'Fischer',
                'orcid': '0000-0004-4567-8901',
                'affiliation': 'Helmholtz-Zentrum',
                'research_field': 'Immunologie',
                'is_staff': False,
                'is_superuser': False
            },
            # Moderator
            {
                'username': 'seed_moderator',
                'email': 'moderator@example.com',
                'first_name': 'Julia',
                'last_name': 'Becker',
                'orcid': '0000-0005-5678-9012',
                'affiliation': 'Leopoldina',
                'research_field': 'Wissenschaftskommunikation',
                'is_staff': True,
                'is_superuser': False
            },
            # Review Editor
            {
                'username': 'seed_editor',
                'email': 'editor@example.com',
                'first_name': 'Michael',
                'last_name': 'Schneider',
                'orcid': '0000-0006-6789-0123',
                'affiliation': 'Leopoldina',
                'research_field': 'Wissenschaftsethik',
                'is_staff': True,
                'is_superuser': False
            },
            # Editorial Office
            {
                'username': 'seed_editorial',
                'email': 'editorial@example.com',
                'first_name': 'Laura',
                'last_name': 'Hoffmann',
                'orcid': '0000-0007-7890-1234',
                'affiliation': 'Leopoldina',
                'research_field': 'Wissenschaftsmanagement',
                'is_staff': True,
                'is_superuser': True
            }
        ]

        users = []
        for data in user_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'orcid': data['orcid'],
                    'affiliation': data['affiliation'],
                    'research_field': data['research_field'],
                    'is_staff': data['is_staff'],
                    'is_superuser': data['is_superuser'],
                    'dsgvo_consent': True,
                    'license_consent': True,
                    'notification_consent': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)

        return users

    def assign_roles(self, users):
        self.stdout.write('Assigning roles to users...')
        # users indices based on creation order in create_users()
        author1, author2 = users[0], users[1]
        commentator1, commentator2 = users[2], users[3]
        moderator = users[4]
        review_editor = users[5]
        editorial_office = users[6]

        groups = {g.name: g for g in Group.objects.all()}
        author1.groups.add(groups['authors'], groups['commentators'])
        author2.groups.add(groups['authors'])
        commentator1.groups.add(groups['commentators'])
        commentator2.groups.add(groups['commentators'])
        moderator.groups.add(groups['moderators'])
        review_editor.groups.add(groups['review_editors'], groups['moderators'])
        editorial_office.groups.add(groups['editorial_office'])

    def create_publications(self, users):
        """Create publications with document versions"""
        self.stdout.write('Creating publications and document versions...')

        publications_data = [
            {
                'title': 'Neue Erkenntnisse zur Genexpression in Säugetierzellen',
                'short_title': 'Genexpression in Säugetierzellen',
                'status': 'published',
                'versions': [
                    {
                        'version_number': 1,
                        'status': 'published',
                        'technical_abstract': 'Diese Studie untersucht die Regulation der Genexpression in Säugetierzellen unter verschiedenen Stressbedingungen.',
                        'non_technical_abstract': 'Wir haben untersucht, wie Zellen auf Stress reagieren und ihre Gene anpassen.',
                        'introduction': 'Die Regulation der Genexpression ist ein fundamentaler Prozess in allen lebenden Organismen...',
                        'methodology': 'Wir haben Zellkulturen von HEK293-Zellen unter verschiedenen Stressbedingungen kultiviert...',
                        'main_text': 'Unsere Ergebnisse zeigen eine signifikante Veränderung der Genexpression unter oxidativem Stress...',
                        'conclusion': 'Diese Studie liefert neue Einblicke in die molekularen Mechanismen der Stressantwort in Säugetierzellen...',
                        'author_contributions': 'A.S. konzipierte die Studie. T.M. führte die Experimente durch. Beide Autoren analysierten die Daten und schrieben das Manuskript.',
                        'conflicts_of_interest': 'Die Autoren erklären, dass keine Interessenkonflikte bestehen.',
                        'acknowledgments': 'Wir danken dem Labor für Molekularbiologie für die technische Unterstützung.',
                        'funding': 'Diese Arbeit wurde durch die Deutsche Forschungsgemeinschaft (Projektnummer 123456) unterstützt.',
                        'references': 'Smith et al. (2020). Gene expression in mammalian cells. Nature, 123, 456-789.\nJones et al. (2019). Stress response in cell cultures. Cell, 456, 789-012.',
                        'keywords': ['Genexpression', 'Stressantwort', 'Säugetierzellen', 'Molekularbiologie']
                    }
                ]
            },
            {
                'title': 'Auswirkungen des Klimawandels auf alpine Ökosysteme',
                'short_title': 'Klimawandel und alpine Ökosysteme',
                'status': 'published',
                'versions': [
                    {
                        'version_number': 1,
                        'status': 'published',
                        'technical_abstract': 'Diese Studie untersucht die Auswirkungen des Klimawandels auf die Biodiversität und Ökosystemfunktionen in alpinen Regionen.',
                        'non_technical_abstract': 'Wir haben untersucht, wie sich der Klimawandel auf Pflanzen und Tiere in den Alpen auswirkt.',
                        'introduction': 'Alpine Ökosysteme gehören zu den am stärksten vom Klimawandel betroffenen Lebensräumen...',
                        'methodology': 'Wir haben Langzeitdaten aus 20 alpinen Standorten in den europäischen Alpen analysiert...',
                        'main_text': 'Die Ergebnisse zeigen eine durchschnittliche Temperaturerhöhung von 1,5°C in den letzten 30 Jahren...',
                        'conclusion': 'Unsere Studie belegt signifikante Veränderungen in der Artenzusammensetzung und Phänologie alpiner Pflanzengemeinschaften...',
                        'author_contributions': 'A.S. und T.M. konzipierten die Studie. Alle Autoren trugen zur Datenerhebung, Analyse und zum Schreiben des Manuskripts bei.',
                        'conflicts_of_interest': 'Die Autoren erklären, dass keine Interessenkonflikte bestehen.',
                        'acknowledgments': 'Wir danken den Nationalparkverwaltungen für die Unterstützung bei der Feldarbeit.',
                        'funding': 'Diese Arbeit wurde durch das Bundesministerium für Bildung und Forschung (Förderkennzeichen 987654) unterstützt.',
                        'references': 'Brown et al. (2018). Climate change impacts on alpine ecosystems. Ecology, 789, 012-345.\nGreen et al. (2020). Biodiversity shifts in mountain regions. Nature Climate Change, 345, 678-901.',
                        'keywords': ['Klimawandel', 'Alpine Ökosysteme', 'Biodiversität', 'Ökologie']
                    },
                    {
                        'version_number': 2,
                        'status': 'published',
                        'technical_abstract': 'Diese aktualisierte Studie erweitert die Analyse der Auswirkungen des Klimawandels auf alpine Ökosysteme mit neuen Daten aus den Jahren 2020-2022.',
                        'non_technical_abstract': 'Wir haben unsere Untersuchung zu den Auswirkungen des Klimawandels auf die Alpen mit neuen Daten aktualisiert.',
                        'introduction': 'Alpine Ökosysteme gehören zu den am stärksten vom Klimawandel betroffenen Lebensräumen...',
                        'methodology': 'Wir haben Langzeitdaten aus 25 alpinen Standorten in den europäischen Alpen analysiert, einschließlich neuer Standorte in den Ostalpen...',
                        'main_text': 'Die aktualisierten Ergebnisse bestätigen den Trend einer durchschnittlichen Temperaturerhöhung, die nun bei 1,8°C in den letzten 32 Jahren liegt...',
                        'conclusion': 'Die erweiterte Analyse bestätigt und verstärkt unsere früheren Erkenntnisse zu den signifikanten Veränderungen in alpinen Ökosystemen...',
                        'author_contributions': 'A.S. und T.M. konzipierten die Studie. Alle Autoren trugen zur Datenerhebung, Analyse und zum Schreiben des Manuskripts bei.',
                        'conflicts_of_interest': 'Die Autoren erklären, dass keine Interessenkonflikte bestehen.',
                        'acknowledgments': 'Wir danken den Nationalparkverwaltungen für die Unterstützung bei der Feldarbeit.',
                        'funding': 'Diese Arbeit wurde durch das Bundesministerium für Bildung und Forschung (Förderkennzeichen 987654) unterstützt.',
                        'references': 'Brown et al. (2018). Climate change impacts on alpine ecosystems. Ecology, 789, 012-345.\nGreen et al. (2020). Biodiversity shifts in mountain regions. Nature Climate Change, 345, 678-901.\nSmith et al. (2022). Recent acceleration of climate change impacts in mountain ecosystems. Science, 567, 890-123.',
                        'keywords': ['Klimawandel', 'Alpine Ökosysteme', 'Biodiversität', 'Ökologie', 'Langzeitmonitoring']
                    }
                ]
            }
        ]

        publications = []
        for pub_data in publications_data:
            # Create publication
            meta_doi = f"10.seed/{uuid.uuid4().hex[:8]}"
            publication, created = Publication.objects.get_or_create(
                meta_doi=meta_doi,
                defaults={
                    'title': pub_data['title'],
                    'short_title': pub_data['short_title'],
                    'status': pub_data['status'],
                    'editorial_board': users[5]  # Review Editor
                }
            )

            # Create document versions
            for version_data in pub_data['versions']:
                doi = f"{meta_doi}/v{version_data['version_number']}"
                document_version, created = DocumentVersion.objects.get_or_create(
                    publication=publication,
                    version_number=version_data['version_number'],
                    defaults={
                        'doi': doi,
                        'status': version_data['status'],
                        'technical_abstract': version_data['technical_abstract'],
                        'non_technical_abstract': version_data['non_technical_abstract'],
                        'introduction': version_data['introduction'],
                        'methodology': version_data['methodology'],
                        'main_text': version_data['main_text'],
                        'conclusion': version_data['conclusion'],
                        'author_contributions': version_data['author_contributions'],
                        'conflicts_of_interest': version_data['conflicts_of_interest'],
                        'acknowledgments': version_data['acknowledgments'],
                        'funding': version_data['funding'],
                        'references': version_data['references'],
                        'content': f"{version_data['introduction']}\n\n{version_data['methodology']}\n\n{version_data['main_text']}\n\n{version_data['conclusion']}",
                        'status_user': users[6],  # Editorial Office
                        'release_date': timezone.now().date() - timedelta(days=random.randint(1, 30)),
                        'status_date': timezone.now() - timedelta(days=random.randint(1, 30))
                    }
                )

                # Create authors for document version
                if created:
                    # First author
                    Author.objects.create(
                        document_version=document_version,
                        name=f"{users[0].first_name} {users[0].last_name}",
                        email=users[0].email,
                        institution=users[0].affiliation,
                        orcid=users[0].orcid,
                        user=users[0],
                        order=1,
                        is_corresponding=True
                    )

                    # Second author
                    Author.objects.create(
                        document_version=document_version,
                        name=f"{users[1].first_name} {users[1].last_name}",
                        email=users[1].email,
                        institution=users[1].affiliation,
                        orcid=users[1].orcid,
                        user=users[1],
                        order=2,
                        is_corresponding=False
                    )

                    # Create keywords
                    for keyword_text in version_data['keywords']:
                        Keyword.objects.create(
                            document_version=document_version,
                            keyword=keyword_text
                        )

            publications.append(publication)

        return publications

    def create_comments(self, users, publications):
        """Create comments on document versions"""
        self.stdout.write('Creating comments...')

        # Get comment types
        sc_type = CommentType.objects.get(code='SC')
        rsc_type = CommentType.objects.get(code='rSC')
        er_type = CommentType.objects.get(code='ER')
        ad_type = CommentType.objects.get(code='AD')
        np_type = CommentType.objects.get(code='NP')

        # Create comments for each publication's latest version
        for publication in publications:
            document_version = publication.latest_version()

            # Scientific Comment (SC)
            sc_comment = Comment.objects.create(
                document_version=document_version,
                comment_type=sc_type,
                content="Könnte die beobachtete Veränderung nicht auch auf andere Faktoren zurückzuführen sein, die in der Studie nicht berücksichtigt wurden?",
                section_reference="Methodology",
                line_start=10,
                line_end=15,
                status='published',
                doi=f"10.seed/comment/{uuid.uuid4().hex[:8]}",
                status_date=timezone.now() - timedelta(days=random.randint(1, 15)),
                status_user=users[4]  # Moderator
            )

            # Create comment author
            CommentAuthor.objects.create(
                comment=sc_comment,
                user=users[2],  # Commentator 1
                is_corresponding=True
            )

            # Create comment reference
            CommentReference.objects.create(
                comment=sc_comment,
                title="Alternative explanations for observed changes in complex systems",
                authors="Johnson et al.",
                publication_date=timezone.now().date() - timedelta(days=365),
                doi="10.1234/science.abc123",
                citation_text="Johnson et al. (2022). Alternative explanations for observed changes in complex systems. Science, 567, 890-123.",
                trust_level="high"
            )

            # Create conflict of interest
            ConflictOfInterest.objects.create(
                comment=sc_comment,
                statement="None",
                has_conflict=False
            )

            # Create comment moderation
            CommentModeration.objects.create(
                comment=sc_comment,
                moderator=users[4],  # Moderator
                decision='approved',
                decision_reason="Comment meets all formal requirements and is relevant to the publication."
            )

            # Response to Scientific Comment (rSC)
            rsc_comment = Comment.objects.create(
                document_version=document_version,
                parent_comment=sc_comment,
                comment_type=rsc_type,
                content="Danke für den wichtigen Hinweis. Wir haben in unserer Methodik tatsächlich mehrere Kontrollvariablen einbezogen, die in Abschnitt 2.3 beschrieben sind. Könnten Sie spezifizieren, welche zusätzlichen Faktoren Ihrer Meinung nach berücksichtigt werden sollten?",
                status='published',
                doi=f"10.seed/comment/{uuid.uuid4().hex[:8]}",
                status_date=timezone.now() - timedelta(days=random.randint(1, 10)),
                status_user=users[4]  # Moderator
            )

            # Create comment author (author responding)
            CommentAuthor.objects.create(
                comment=rsc_comment,
                user=users[0],  # Author 1
                is_corresponding=True
            )

            # Create comment moderation
            CommentModeration.objects.create(
                comment=rsc_comment,
                moderator=users[4],  # Moderator
                decision='approved',
                decision_reason="Response is appropriate and continues the scientific discussion."
            )

            # Error Correction (ER)
            er_comment = Comment.objects.create(
                document_version=document_version,
                comment_type=er_type,
                content="Gibt es einen Tippfehler in Tabelle 2? Der p-Wert sollte vermutlich 0,003 statt 0,03 sein, wenn man die Freiheitsgrade berücksichtigt?",
                section_reference="Results",
                line_start=45,
                line_end=45,
                status='published',
                status_date=timezone.now() - timedelta(days=random.randint(1, 5)),
                status_user=users[4]  # Moderator
            )

            # Create comment author
            CommentAuthor.objects.create(
                comment=er_comment,
                user=users[3],  # Commentator 2
                is_corresponding=True
            )

            # Create comment moderation
            CommentModeration.objects.create(
                comment=er_comment,
                moderator=users[4],  # Moderator
                decision='approved',
                decision_reason="Valid error correction."
            )

            # Additional Data (AD)
            ad_comment = Comment.objects.create(
                document_version=document_version,
                comment_type=ad_type,
                content="Haben Sie die kürzlich veröffentlichten Daten von Zhang et al. berücksichtigt, die ähnliche Effekte in einem anderen System zeigen?",
                section_reference="Discussion",
                line_start=70,
                line_end=75,
                status='published',
                doi=f"10.seed/comment/{uuid.uuid4().hex[:8]}",
                status_date=timezone.now() - timedelta(days=random.randint(1, 8)),
                status_user=users[4]  # Moderator
            )

            # Create comment author
            CommentAuthor.objects.create(
                comment=ad_comment,
                user=users[2],  # Commentator 1
                is_corresponding=True
            )

            # Create comment reference
            CommentReference.objects.create(
                comment=ad_comment,
                title="Comparative analysis of system responses under varying conditions",
                authors="Zhang et al.",
                publication_date=timezone.now().date() - timedelta(days=180),
                doi="10.5678/nature.def456",
                citation_text="Zhang et al. (2023). Comparative analysis of system responses under varying conditions. Nature, 789, 123-456.",
                trust_level="high"
            )

            # Create comment moderation
            CommentModeration.objects.create(
                comment=ad_comment,
                moderator=users[4],  # Moderator
                decision='approved',
                decision_reason="Relevant additional data that enhances the discussion."
            )

            # New Publication (NP)
            np_comment = Comment.objects.create(
                document_version=document_version,
                comment_type=np_type,
                content="Ist Ihnen die neue Veröffentlichung von Garcia et al. bekannt, die einen ähnlichen Ansatz verwendet, aber zu leicht abweichenden Ergebnissen kommt?",
                section_reference="Conclusion",
                line_start=90,
                line_end=95,
                status='published',
                doi=f"10.seed/comment/{uuid.uuid4().hex[:8]}",
                status_date=timezone.now() - timedelta(days=random.randint(1, 3)),
                status_user=users[4]  # Moderator
            )

            # Create comment author
            CommentAuthor.objects.create(
                comment=np_comment,
                user=users[3],  # Commentator 2
                is_corresponding=True
            )

            # Create comment reference
            CommentReference.objects.create(
                comment=np_comment,
                title="Alternative methodological approach to system analysis",
                authors="Garcia et al.",
                publication_date=timezone.now().date() - timedelta(days=90),
                doi="10.9012/science.ghi789",
                citation_text="Garcia et al. (2023). Alternative methodological approach to system analysis. Science Advances, 456, 789-012.",
                trust_level="high"
            )

            # Create comment moderation
            CommentModeration.objects.create(
                comment=np_comment,
                moderator=users[4],  # Moderator
                decision='approved',
                decision_reason="Relevant new publication that contributes to the scientific discussion."
            )
