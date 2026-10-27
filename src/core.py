"""Boot splash themes for SigmaOS-plymouth.

Principles: pure plan layer (theme files are described and validated, not
installed by plan functions except via an isolated store), fail-fast on
unknown themes and missing sources, deterministic rendering, KISS.
"""
import argparse, os, re, shutil, sys

ENGINE = {
    "name": "sigma-plymouth",
    "summary": "Manage, preview and build boot splash themes",
    "language": "python",
    "verbs": ["themes", "set", "preview", "build"],
    "principles": ["Pure Plan / Thin Execute", "Fail-Fast",
                   "Deterministic Testing", "KISS", "DRY"],
}

cli_doc = """\
$ sigma-plymouth themes
$ sigma-plymouth set sigma-dark --config ./plymouthd.conf
$ sigma-plymouth preview sigma-dark --width 48 --frame 3
$ sigma-plymouth build ./theme-src --name sigma-aurora
"""

THEMES = {
    "sigma-aurora": {"type": "script", "duration": 8.0, "transition": "fade"},
    "sigma-spinner": {"type": "script", "duration": 5.0, "transition": "rotate"},
    "sigma-text": {"type": "text", "duration": 0.0, "transition": "none"},
}

_THEME_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,32}$")


class PlymouthError(Exception):
    pass


def themes():
    """Pure: sorted list of built-in themes with metadata."""
    return [{"name": name, **THEMES[name]} for name in sorted(THEMES)]


def check_theme(name):
    if name not in THEMES:
        raise PlymouthError(f"unknown theme: {name!r} (one of {sorted(THEMES)})")
    return name


def daemon_config(theme):
    """Pure: render the [Daemon] block for plymouthd.conf."""
    check_theme(theme)
    return f"[Daemon]\nTheme={theme}\nShowDelay=0\nDeviceTimeout=8\n"


def set_theme(config_path, theme):
    """Side-effecting but isolated: write the daemon config at config_path.

    Only touches the given path (tests pass a tempfile); the real
    /etc/plymouthd.conf is never used by self_test.
    """
    text = daemon_config(theme)
    tmp = config_path + ".sigma-tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, config_path)
    return text


def preview(theme, width=40, frame=0):
    """Pure: deterministic ASCII progress frame for a theme."""
    check_theme(theme)
    if not isinstance(width, int) or isinstance(width, bool) or not (10 <= width <= 200):
        raise PlymouthError(f"width must be 10..200, got {width!r}")
    if not isinstance(frame, int) or isinstance(frame, bool) or frame < 0:
        raise PlymouthError(f"bad frame: {frame!r}")
    if THEMES[theme]["type"] == "text":
        return "Starting SigmaOS..."
    filled = (frame * 7) % (width + 1)  # deterministic pseudo-progress
    bar = "#" * filled + "-" * (width - filled)
    glyph = "*" if THEMES[theme]["transition"] == "rotate" else ">"
    return f"[{bar}] {glyph} {theme}"


def build_plan(source_dir, name):
    """Pure: validate theme sources and return ordered build/install steps."""
    if not _THEME_NAME_RE.match(name):
        raise PlymouthError(f"bad theme name: {name!r}")
    if not os.path.isdir(source_dir):
        raise PlymouthError(f"no such source directory: {source_dir}")
    required = [f"{name}.plymouth", f"{name}.script"]
    missing = [f for f in required
               if not os.path.isfile(os.path.join(source_dir, f))]
    if missing:
        raise PlymouthError("missing theme file(s): " + ", ".join(missing))
    steps = [
        {"step": "validate", "cmd": f"plymouth --check --theme-dir {source_dir}"},
        {"step": "compile", "cmd": f"plymouth-set-default --install {name}"
                                   f" --source-dir {source_dir}"},
        {"step": "register", "cmd": f"update-alternatives --install "
                                    f"/usr/share/plymouth/themes/default {name} 100"},
        {"step": "activate", "cmd": f"plymouth-set-default {name}"},
    ]
    return steps


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=ENGINE["name"], description=ENGINE["summary"])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("themes", help="list built-in themes")
    st = sub.add_parser("set", help="set the active theme in a config file")
    st.add_argument("theme", help="theme name")
    st.add_argument("--config", default="plymouthd.conf",
                    help="target config file (isolated; not the real /etc)")
    pv = sub.add_parser("preview", help="ASCII preview frame")
    pv.add_argument("theme")
    pv.add_argument("--width", type=int, default=40)
    pv.add_argument("--frame", type=int, default=0)
    bd = sub.add_parser("build", help="theme build/install plan")
    bd.add_argument("source_dir")
    bd.add_argument("--name", required=True)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "themes":
            for t in themes():
                print(f"{t['name']}: {t['type']} duration={t['duration']} "
                      f"transition={t['transition']}")
        elif args.cmd == "set":
            set_theme(args.config, args.theme)
            print(f"theme set: {args.theme} -> {args.config}")
        elif args.cmd == "preview":
            print(preview(args.theme, width=args.width, frame=args.frame))
        elif args.cmd == "build":
            for s in build_plan(args.source_dir, args.name):
                print(f"{s['step']}: {s['cmd']}")
        return 0
    except (PlymouthError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def self_test() -> None:
    import tempfile
    # themes listing: sorted, complete metadata
    names = [t["name"] for t in themes()]
    assert names == sorted(names)
    assert names == ["sigma-aurora", "sigma-spinner", "sigma-text"]
    assert all(t["type"] in ("script", "text") for t in themes())
    # set: isolated config file write, idempotent content
    with tempfile.TemporaryDirectory() as d:
        conf = os.path.join(d, "plymouthd.conf")
        set_theme(conf, "sigma-aurora")
        body = open(conf, encoding="utf-8").read()
        assert body == daemon_config("sigma-aurora")
        assert "Theme=sigma-aurora" in body and "[Daemon]" in body
        set_theme(conf, "sigma-spinner")  # overwrite cleanly
        assert "Theme=sigma-spinner" in open(conf, encoding="utf-8").read()
        assert not os.path.exists(conf + ".sigma-tmp")  # atomic replace
        # preview: deterministic, width respected
        p1 = preview("sigma-aurora", width=30, frame=3)
        assert preview("sigma-aurora", width=30, frame=3) == p1  # deterministic
        assert len(p1) >= 30 and "#" in p1 and "-" in p1
        assert "[" in p1 and "]" in p1
        assert preview("sigma-text", width=30) == "Starting SigmaOS..."
        # build plan: needs real-looking sources in an isolated dir
        src = os.path.join(d, "src")
        os.makedirs(src)
        try:
            build_plan(src, "sigma-aurora")
        except PlymouthError as e:
            assert "missing theme file" in str(e)
        else:
            raise AssertionError("missing sources not caught")
        for fname in ("sigma-aurora.plymouth", "sigma-aurora.script"):
            with open(os.path.join(src, fname), "w", encoding="utf-8") as fh:
                fh.write("# theme source\n")
        steps = build_plan(src, "sigma-aurora")
        assert [s["step"] for s in steps] == ["validate", "compile",
                                              "register", "activate"]
        assert all("sigma-aurora" in s["cmd"] for s in steps[1:])
    # fail-fast
    for bad_call in (
        lambda: set_theme("/tmp/x", "no-such-theme"),
        lambda: preview("no-such-theme"),
        lambda: preview("sigma-aurora", width=5),
        lambda: preview("sigma-aurora", width=1000),
        lambda: preview("sigma-aurora", frame=-1),
        lambda: build_plan("/nonexistent-dir-zz", "sigma-aurora"),
        lambda: build_plan("/tmp", "Bad Name"),
    ):
        try:
            bad_call()
        except PlymouthError:
            pass
        else:
            raise AssertionError("expected PlymouthError")
    # CLI smoke through main()
    with tempfile.TemporaryDirectory() as d:
        conf = os.path.join(d, "plymouthd.conf")
        assert main(["themes"]) == 0
        assert main(["set", "sigma-dark", "--config", conf]) == 1  # unknown theme
        assert main(["set", "sigma-spinner", "--config", conf]) == 0
        assert main(["preview", "sigma-spinner", "--width", "20", "--frame", "2"]) == 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
