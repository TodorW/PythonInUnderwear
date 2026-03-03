try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


class TemplateEngine:
    def __init__(self, template_dir: str = "templates"):
        if not JINJA2_AVAILABLE:
            raise RuntimeError(
                "Jinja2 is required for template rendering.\n"
                "Install it with: pip install jinja2"
            )
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"])
        )

    def render(self, template_name: str, **context) -> str:
        tmpl = self.env.get_template(template_name)
        return tmpl.render(**context)

    def render_string(self, source: str, **context) -> str:
        """Render a raw template string instead of a file."""
        tmpl = self.env.from_string(source)
        return tmpl.render(**context)

    def __repr__(self):
        return f"<TemplateEngine dir={self.env.loader.searchpath}>"