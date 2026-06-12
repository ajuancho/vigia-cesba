"""Los emails (digest + invitación) deben escapar texto controlable por
usuario/terceros (nombre de workspace, quién invita, títulos de normas scrapeados)
para no permitir inyección de HTML/links en el cliente de correo."""
from vigia_workers.notifications import render_digest, render_invitation


def test_render_digest_escapes_user_controlled_html():
    items = [
        {
            "id": 1,
            "keyword": "<script>",
            "tipo": "Ley",
            "numero": "27000",
            "titulo": '<img src=x onerror=alert(1)>',
        }
    ]
    out = render_digest("<b>Acme & Co</b>", items)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "<img src=x" not in out
    assert "&lt;img" in out
    assert "&lt;b&gt;Acme &amp; Co&lt;/b&gt;" in out
    # el link legítimo a la norma sigue intacto
    assert "/norma/1" in out


def test_render_digest_pluraliza_coincidencias():
    item = {"id": 1, "keyword": "minería", "tipo": "Ley", "numero": "27000", "titulo": "T"}
    assert "Se detectó 1 coincidencia con tus alertas" in render_digest("WS", [item])
    out = render_digest("WS", [item, {**item, "id": 2}])
    assert "Se detectaron 2 coincidencias con tus alertas" in out


def test_render_invitation_escapes_user_controlled_html():
    accept_url = "https://vigia.openarg.org/auth/invite?token=abc123"
    out = render_invitation(
        "<b>WS</b>", "<i>admin</i>", accept_url, invited_by="<script>x</script>"
    )
    assert "<script>x</script>" not in out
    assert "&lt;script&gt;" in out
    assert "&lt;b&gt;WS&lt;/b&gt;" in out
    assert "&lt;i&gt;admin&lt;/i&gt;" in out
    # el accept_url legítimo NO debe romperse
    assert accept_url in out
