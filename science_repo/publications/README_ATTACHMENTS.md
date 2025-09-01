Attachments image upload API for editor paste/drop

Endpoint
- POST /api/publications/attachments/upload-image/
- Content-Type: multipart/form-data
- Auth: required (author of the document)

Form fields
- file (required): image file (png, jpeg, webp, svg)
- document_version (optional, int): ID to associate the attachment
- title (optional): default = filename
- description (optional)

Validation & processing
- MIME whitelist: image/png, image/jpeg, image/webp, image/svg+xml
- Size limit: MAX_UPLOAD_IMAGE_SIZE_MB (default 15 MB)
- ClamAV: REQUIRED (network scan via clamd INSTREAM). If CLAMAV_HOST/PORT not configured: 503 Service Unavailable.
- EXIF: removed by re-encoding via Pillow (JPEG/PNG/WEBP supported; SVG passthrough). Orientation normalized; ICC preserved.

Response 201 JSON
{
  "id": <int>,
  "url": "https://cdn-or-media-url/...",
  "mime": "image/png",
  "size": 123456,
  "width": 1200,
  "height": 800,
  "checksum_sha256": "...",
  "exif_removed": true,
  "w": 1200,
  "h": 800,
  "hash": "..."
}

Follow-up (optional)
- Create a Figure via POST /api/publications/figures/ with fields:
  - document_version: int
  - title: string
  - caption: text
  - alt_text: string
  - license: string
  - source: string
  - attribution: string
  - image: (use direct upload OR your client can send the URL via a separate upload step; typically you upload the image directly as part of Figure too)

JATS Export
- Figures are exported under `<body><sec sec-type="figures">` with:
  - `<fig id="figN">` containing `<caption><p>...</p></caption>`, optional `<alt-text>`, and `<graphic xlink:href="..."/>`
  - license/source/attribution are emitted as data-* attributes for now.

Notes for frontend (Tiptap/ProseMirror)
- Implement an onPaste/onDrop handler that:
  1) extracts files or data URLs from clipboard (Word/Web/Screenshot),
  2) converts data URLs to File if necessary,
  3) POSTs the File to /attachments/upload-image/ to obtain the final URL,
  4) inserts a Figure node in the editor, then opens a modal to fill caption, alt_text, license, source, attribution.
- Optional: After the dialog, call POST /figures/ to persist the figure metadata linked to the current document_version.

Example handler (TypeScript sketch):
```
import { Editor } from '@tiptap/react'

async function uploadImage(file: File, documentVersionId?: number) {
  const fd = new FormData()
  fd.append('file', file)
  if (documentVersionId) fd.append('document_version', String(documentVersionId))
  const res = await fetch('/api/publications/attachments/upload-image/', {
    method: 'POST',
    credentials: 'include',
    body: fd,
  })
  if (!res.ok) throw new Error('Upload failed')
  return await res.json() as { url: string, width?: number, height?: number }
}

export function makePasteHandler(editor: Editor, documentVersionId?: number) {
  return async (event: ClipboardEvent) => {
    const items = event.clipboardData?.items
    if (!items) return
    // Prefer files
    for (const item of items) {
      if (item.kind === 'file') {
        const file = item.getAsFile()
        if (file && file.type.startsWith('image/')) {
          event.preventDefault()
          const meta = await uploadImage(file, documentVersionId)
          // Insert your Figure node with placeholder metadata
          editor.chain().focus().insertContent({
            type: 'figure',
            attrs: {
              src: meta.url,
              alt_text: '',
              caption: '',
              license: '',
              source: '',
              attribution: '',
            },
          }).run()
          // Open your figure dialog to collect caption/alt/license/source/attribution
          return
        }
      }
      if (item.kind === 'string') {
        const type = item.type
        if (type === 'text/html' || type === 'text/plain') {
          const text = await new Promise<string>(resolve => item.getAsString(resolve))
          // Optional: detect <img src="data:..."> or URLs, fetch to Blob, then call uploadImage()
        }
      }
    }
  }
}
```


## OpenAPI Sketch (YAML)

```yaml
openapi: 3.0.3
info:
  title: Assets Upload
  version: '1.0'
paths:
  /api/publications/attachments/upload-image/:
    post:
      summary: Upload image from paste/drop
      description: |
        Uploads an image, performs mandatory ClamAV scan, strips EXIF (except SVG),
        and stores the file. Returns final URL and metadata. Requires authentication.
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file]
              properties:
                file:
                  type: string
                  format: binary
                  description: Image file (png, jpeg, webp, svg)
                document_version:
                  type: integer
                  nullable: true
                title:
                  type: string
                description:
                  type: string
      responses:
        '201':
          description: Created
          content:
            application/json:
              schema:
                type: object
                properties:
                  id: { type: integer }
                  url: { type: string, format: uri }
                  mime: { type: string, enum: [image/png, image/jpeg, image/webp, image/svg+xml] }
                  size: { type: integer }
                  width: { type: integer, nullable: true }
                  height: { type: integer, nullable: true }
                  w: { type: integer, nullable: true }
                  h: { type: integer, nullable: true }
                  checksum_sha256: { type: string }
                  hash: { type: string }
                  exif_removed: { type: boolean }
        '400':
          description: Bad Request (validation error)
        '503':
          description: Service Unavailable (ClamAV not configured or scan failed)
      security:
        - cookieAuth: []
components:
  securitySchemes:
    cookieAuth:
      type: apiKey
      in: cookie
      name: sessionid
```

Notes:
- Alt-text is mandatory when creating Figures via /api/publications/figures/ (server-side validation).
- Figure attributes to use in the editor node: {src,url,width,height,hash,caption,alt,license,source,attribution}.
