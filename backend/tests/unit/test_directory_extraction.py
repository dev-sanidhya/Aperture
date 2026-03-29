from app.integrations.discovery.directories import DirectoryClient


def test_directory_parser_extracts_contacts_and_website() -> None:
    html = """
    <html>
      <head><title>Example Biz - Justdial</title></head>
      <body>
        <a href="tel:+91 9988776655">Call</a>
        <a href="mailto:owner@examplebiz.in">Email</a>
        <a href="https://examplebiz.in">Website</a>
        <a href="https://wa.me/919988776655">WhatsApp</a>
        <a href="https://facebook.com/examplebiz">Facebook</a>
      </body>
    </html>
    """
    extraction = DirectoryClient()._parse("https://www.justdial.com/mumbai/example", html)
    assert "+919988776655" in extraction.phones
    assert "owner@examplebiz.in" in extraction.emails
    assert "https://examplebiz.in" in extraction.website_urls
    assert "+919988776655" in extraction.whatsapp_numbers
    assert any("facebook.com" in link for link in extraction.social_links)

