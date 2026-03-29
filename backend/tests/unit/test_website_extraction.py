from app.integrations.discovery.websites import WebsiteClient


def test_parse_page_extracts_contacts_and_social_links() -> None:
    html = """
    <html>
      <body>
        <a href="mailto:hello@example.com">Email</a>
        <a href="tel:+91 9876543210">Call</a>
        <a href="https://wa.me/919876543210">WhatsApp</a>
        <a href="/contact">Contact</a>
        <a href="https://instagram.com/examplebiz">Instagram</a>
      </body>
    </html>
    """
    extraction = WebsiteClient()._parse_page("https://example.com", html)
    assert "hello@example.com" in extraction.emails
    assert "+919876543210" in extraction.phones
    assert "+919876543210" in extraction.whatsapp_numbers
    assert "https://example.com/contact" in extraction.contact_pages
    assert any("instagram.com" in link for link in extraction.social_links)

