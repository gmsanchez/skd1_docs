# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = "SKD-1"
author = "SKD-1 team"
copyright = "SKD-1 team, adapted from the Nav2 documentation (Apache-2.0)"

extensions = [
    "myst_parser",             # Markdown support
    "sphinxcontrib.mermaid",   # Mermaid diagrams
]

# --- Markdown (MyST) ---------------------------------------------------------
myst_enable_extensions = [
    "alert",        # GitHub-style alerts: > [!NOTE], > [!WARNING], ...
    "colon_fence",  # ::: fences, if you ever need directives in Markdown
]
myst_heading_anchors = 3
# Render ```mermaid fences as diagrams (GitHub renders them natively too)
myst_fence_as_directive = ["mermaid"]

source_suffix = {".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "requirements.txt"]

# --- HTML output -------------------------------------------------------------
html_theme = "furo"
html_title = "SKD-1 documentation"
html_theme_options = {
    # Adjust to the real repository name and branch
    "source_repository": "https://github.com/gmsanchez/skd1_docs/",
    "source_branch": "main",
    "source_directory": "docs/",
}
