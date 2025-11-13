from importlib.metadata import version, PackageNotFoundError

SYMBOL_BANNER = (r"""
     .--------.
    / .------. \
   / /        \ \
   | |        | |
  _| |________| |_
.' |_|        |_| '.
'._____ ____ _____.'
|     .'____'.     |
'.__.'.'    '.'.__.'
'.__  |  OG  |  __.'
|   '.'.____.'.'   |
'.____'.____.'____.'OldieGoldie by Venu
'.________________.'    
""")


def version_banner(app_name: str):
    """Return a banner string with version info."""
    try:
        pkg_version = version("oldie-goldie")
    except PackageNotFoundError:
        pkg_version = "dev"

    banner = f"""
╔═════════════════════════════════════════════════╗
║   🟡 {app_name} — Oldie Goldie v{pkg_version}   
╚═════════════════════════════════════════════════╝
"""
    return banner + "\n" + SYMBOL_BANNER
