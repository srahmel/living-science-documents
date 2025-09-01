import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings
import time
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DOIService:
    """
    DataCite Fabrica REST integration (sandbox-ready) for DOI lifecycle:
    - Generate deterministic DOIs using PREFIX
    - Create draft DOI, update metadata, set findable (publish), set registered (withdraw/undo)
    - Retry with exponential backoff, idempotency via X-Request-Id
    - Resolver verification against https://doi.org/{doi}
    """

    BASE_URL = getattr(settings, 'DATACITE_BASE_URL', 'https://api.test.datacite.org')

    @staticmethod
    def _enabled():
        return getattr(settings, 'DATACITE_ENABLED', False)

    @staticmethod
    def generate_doi(prefix=None, entity_type=None, entity_id=None):
        prefix = prefix or getattr(settings, 'DATACITE_PREFIX', getattr(settings, 'DOI_PREFIX', '10.1234'))
        if entity_type and entity_id:
            return f"{prefix}/lsd.{entity_type}.{entity_id}"
        random_suffix = uuid.uuid4().hex[:8]
        return f"{prefix}/lsd.{random_suffix}"

    @staticmethod
    def validate_doi(doi: str) -> bool:
        if not doi or not isinstance(doi, str):
            return False
        if not doi.startswith('10.'):
            return False
        parts = doi.split('/')
        return len(parts) == 2 and all(parts)

    # -------- DataCite REST helpers --------
    @classmethod
    def _auth(cls):
        cid = getattr(settings, 'DATACITE_SANDBOX_CLIENT_ID', None) or getattr(settings, 'DATACITE_CLIENT_ID', None)
        sec = getattr(settings, 'DATACITE_SANDBOX_CLIENT_SECRET', None) or getattr(settings, 'DATACITE_CLIENT_SECRET', None)
        return HTTPBasicAuth(cid, sec) if cid and sec else None

    @classmethod
    def _headers(cls, request_id: str = None):
        h = {
            'Content-Type': 'application/vnd.api+json',
            'Accept': 'application/vnd.api+json',
        }
        if request_id:
            h['X-Request-Id'] = request_id
        return h

    @classmethod
    def _request(cls, method: str, path: str, json: dict = None, request_id: str = None, max_retries: int = 3, backoff_base: float = 0.5):
        url = f"{cls.BASE_URL}{path}"
        auth = cls._auth()
        if not auth:
            raise RuntimeError('DataCite credentials are not configured')
        attempt = 0
        last_exc = None
        while attempt < max_retries:
            try:
                resp = requests.request(method, url, json=json, headers=cls._headers(request_id), auth=auth, timeout=15)
                if 500 <= resp.status_code < 600:
                    raise RuntimeError(f"DataCite 5xx: {resp.status_code} {resp.text}")
                return resp
            except Exception as e:
                last_exc = e
                attempt += 1
                if attempt >= max_retries:
                    break
                sleep_s = backoff_base * (2 ** (attempt - 1))
                logger.warning(f"DataCite request failed (attempt {attempt}) {method} {path}: {e}. Retrying in {sleep_s}s")
                time.sleep(sleep_s)
        if isinstance(last_exc, Exception):
            raise last_exc
        raise RuntimeError('Unknown DataCite request error')

    # -------- Payload mapping --------
    @staticmethod
    def _creator_from_author(author) -> dict:
        name = author.name or (author.user.get_full_name() if author.user else None) or (author.user.username if author.user else None) or "Unknown"
        creator = {"name": name}
        # nameIdentifiers with ORCID URL
        if author.orcid:
            orcid = author.orcid.strip()
            if not orcid.startswith('http'):
                orcid = f"https://orcid.org/{orcid}"
            creator["nameIdentifiers"] = [{
                "nameIdentifier": orcid,
                "nameIdentifierScheme": "ORCID",
                "schemeUri": "https://orcid.org"
            }]
        # affiliation if available
        if getattr(author, 'institution', None):
            creator["affiliation"] = [{"name": author.institution}]
        return creator

    @classmethod
    def build_attributes_for_version(cls, document_version) -> dict:
        publication = document_version.publication
        title = publication.title
        year = (document_version.release_date or datetime.utcnow().date()).year
        types = {"resourceTypeGeneral": "Text"}
        # landing page URL from settings FRONTEND_URL
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000').rstrip('/')
        landing = f"{base_url}/publication/{publication.id}?version={document_version.version_number}"
        # relatedIdentifiers: concept/meta DOI as IsVersionOf if available
        related = []
        if publication.meta_doi:
            related.append({
                "relationType": "IsVersionOf",
                "relatedIdentifierType": "DOI",
                "relatedIdentifier": publication.meta_doi
            })
        creators = [cls._creator_from_author(a) for a in document_version.authors.all()]
        if not creators:
            # fallback: use status_user
            su = document_version.status_user
            if su:
                creators = [{"name": su.get_full_name() or su.username}]
            else:
                creators = [{"name": "Unknown"}]
        publisher = getattr(settings, 'DATACITE_PUBLISHER', 'Leopoldina – Nationale Akademie der Wissenschaften')
        return {
            "doi": document_version.doi,
            "titles": [{"title": title}],
            "creators": creators,
            "publisher": publisher,
            "publicationYear": year,
            "types": types,
            "url": landing,
            "relatedIdentifiers": related
        }

    # -------- Public API --------
    @classmethod
    def ensure_draft(cls, document_version, request_id: str = None) -> dict:
        if not cls._enabled():
            return {"state": "draft", "doi": document_version.doi}
        payload = {"data": {"type": "dois", "attributes": {"doi": document_version.doi}}}
        resp = cls._request('POST', '/dois', json=payload, request_id=request_id)
        if resp.status_code in (200, 201):
            return resp.json().get('data', {}).get('attributes', {})
        if resp.status_code == 409:
            # Already exists
            return {"state": "draft", "doi": document_version.doi}
        raise RuntimeError(f"Failed to create draft DOI: {resp.status_code} {resp.text}")

    @classmethod
    def update_metadata(cls, document_version, request_id: str = None) -> dict:
        if not cls._enabled():
            return {"state": getattr(document_version, 'doi_status', 'draft'), "doi": document_version.doi}
        attrs = cls.build_attributes_for_version(document_version)
        payload = {"data": {"type": "dois", "attributes": attrs}}
        resp = cls._request('PUT', f"/dois/{document_version.doi}", json=payload, request_id=request_id)
        if resp.status_code in (200, 201):
            return resp.json().get('data', {}).get('attributes', {})
        raise RuntimeError(f"Failed to update DOI metadata: {resp.status_code} {resp.text}")

    @classmethod
    def set_findable(cls, doi: str, request_id: str = None) -> dict:
        if not cls._enabled():
            return {"state": "findable", "doi": doi}
        payload = {"data": {"type": "dois", "attributes": {"event": "publish"}}}
        resp = cls._request('PATCH', f"/dois/{doi}", json=payload, request_id=request_id)
        if resp.status_code in (200, 201):
            return resp.json().get('data', {}).get('attributes', {})
        raise RuntimeError(f"Failed to set DOI findable: {resp.status_code} {resp.text}")

    @classmethod
    def set_registered(cls, doi: str, request_id: str = None) -> dict:
        if not cls._enabled():
            return {"state": "registered", "doi": doi}
        payload = {"data": {"type": "dois", "attributes": {"event": "register"}}}
        resp = cls._request('PATCH', f"/dois/{doi}", json=payload, request_id=request_id)
        if resp.status_code in (200, 201):
            return resp.json().get('data', {}).get('attributes', {})
        raise RuntimeError(f"Failed to set DOI registered: {resp.status_code} {resp.text}")

    @staticmethod
    def get_doi_url(doi: str) -> str:
        return f"https://doi.org/{doi}"

    @classmethod
    def verify_resolver(cls, doi: str, max_retries: int = 3, backoff_base: float = 0.5) -> bool:
        url = cls.get_doi_url(doi)
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, timeout=15, allow_redirects=True)
                if 200 <= resp.status_code < 400:
                    return True
            except Exception as e:
                logger.warning(f"Resolver check failed for {doi} (attempt {attempt+1}): {e}")
            time.sleep(backoff_base * (2 ** attempt))
        return False

    @classmethod
    def verify_landing(cls, landing_url: str, max_retries: int = 3, backoff_base: float = 0.5) -> bool:
        """Verify landing page is reachable (HTTP 200) before making DOI findable."""
        for attempt in range(max_retries):
            try:
                resp = requests.get(landing_url, timeout=10, allow_redirects=True)
                if 200 <= resp.status_code < 300:
                    return True
            except Exception as e:
                logger.warning(f"Landing page check failed for {landing_url} (attempt {attempt+1}): {e}")
            time.sleep(backoff_base * (2 ** attempt))
        return False

    # -------- High-level flows --------
    @classmethod
    def publish_version(cls, document_version) -> str:
        """Create or update DOI for the given version and make it findable. Returns final state."""
        request_id = f"pub-{document_version.id}-{document_version.version_number}"
        logger.info(f"DOI publish start for version {document_version.id} ({document_version.doi})")
        cls.ensure_draft(document_version, request_id=request_id)
        attrs_before = cls.update_metadata(document_version, request_id=request_id)
        landing = attrs_before.get('url') if isinstance(attrs_before, dict) else None
        if not landing:
            # Rebuild landing if not returned by API (when disabled or partial response)
            built = cls.build_attributes_for_version(document_version)
            landing = built.get('url')
        if landing:
            ok_landing = cls.verify_landing(landing)
            if not ok_landing:
                logger.warning(f"Landing page did not return 200 for {landing} before DOI publish")
        attrs = cls.set_findable(document_version.doi, request_id=request_id)
        ok = cls.verify_resolver(document_version.doi)
        if not ok:
            logger.warning(f"DOI resolver did not confirm 200/3xx for {document_version.doi} after publish")
        return attrs.get('state', 'findable')

    @classmethod
    def withdraw_version(cls, document_version) -> str:
        request_id = f"wd-{document_version.id}-{document_version.version_number}"
        logger.info(f"DOI withdraw/update to registered for version {document_version.id} ({document_version.doi})")
        attrs = cls.set_registered(document_version.doi, request_id=request_id)
        return attrs.get('state', 'registered')

    @classmethod
    def update_version_metadata(cls, document_version) -> str:
        request_id = f"upd-{document_version.id}-{document_version.version_number}"
        logger.info(f"DOI metadata update for version {document_version.id} ({document_version.doi})")
        attrs = cls.update_metadata(document_version, request_id=request_id)
        return attrs.get('state', getattr(document_version, 'doi_status', 'draft'))