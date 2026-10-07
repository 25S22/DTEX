#!/usr/bin/env python3
"""
=============================================================
  Dtex Silent Uninstaller Generator  (tested syntax: v6.x)
=============================================================
  INSTRUCTIONS
  ─────────────
  1. Fill in the three variables in the CONFIG block below.
  2. Run:   python generate_dtex_uninstaller.py
  3. A file called  dtex_uninstall.exe  is created next to
     this script — deploy that on the target machine.

  Requirement (one-time, on your admin machine):
      pip install pyinstaller

  Command the generated exe will run silently:
      Release.exe /x // /qn ACCOUNTNAME="<val>" PASSWORD="<val>"
=============================================================
"""

# ╔══════════════════════════════════════════════════════════╗
# ║                     C O N F I G                         ║
# ╚══════════════════════════════════════════════════════════╝

EXE_PATH     = r"C:\path\to\DTEXForwarderWindows-Release.exe"
ACCOUNT_NAME = "your_account_name_here"
PASSWORD     = "your_password_here"

OUTPUT_NAME  = "dtex_uninstall"   # final exe will be  OUTPUT_NAME.exe

# ╔══════════════════════════════════════════════════════════╗
# ║          Do not edit anything below this line           ║
# ╚══════════════════════════════════════════════════════════╝

import sys, os, random, string, tempfile, shutil, subprocess


def _gen_key(n=24):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def _xor(text, key):
    kb = key.encode()
    return [b ^ kb[i % len(kb)] for i, b in enumerate(text.encode())]


def _build_launcher(exe_path, account, password):
    """Return source of the obfuscated launcher — no plaintext credentials."""
    key  = _gen_key()
    e_ex = _xor(exe_path, key)
    e_ac = _xor(account,  key)
    e_pw = _xor(password, key)

    # Documented Dtex 6.x silent uninstall format:
    #   Release.exe /x // /qn ACCOUNTNAME="…" PASSWORD="…"
    # Each list element is passed verbatim — '/qn' has zero leading spaces,
    # and the values are wrapped in double-quotes as required by Dtex.
    return (
        "import subprocess as _s\n"
        "def _r(d,k):\n"
        "    b=k.encode()\n"
        "    return bytes([v^b[i%len(b)]for i,v in enumerate(d)]).decode()\n"
        f"_k={repr(key)}\n"
        f"_a={e_ex}\n"
        f"_b={e_ac}\n"
        f"_c={e_pw}\n"
        "def _m():\n"
        "    x=_r(_a,_k)\n"
        "    n=_r(_b,_k)\n"
        "    p=_r(_c,_k)\n"
        "    _s.run(\n"
        "        [x,'/x','//','/qn',f'ACCOUNTNAME=\"{n}\"',f'PASSWORD=\"{p}\"'],\n"
        "        creationflags=0x08000000,\n"
        "        check=False\n"
        "    )\n"
        "_m()\n"
    )


def main():
    # Basic validation
    if EXE_PATH.startswith("C:\\path\\to\\"):
        print("❌  Please fill in EXE_PATH in the CONFIG section first.")
        sys.exit(1)
    if not ACCOUNT_NAME or ACCOUNT_NAME == "your_account_name_here":
        print("❌  Please fill in ACCOUNT_NAME in the CONFIG section.")
        sys.exit(1)
    if not PASSWORD or PASSWORD == "your_password_here":
        print("❌  Please fill in PASSWORD in the CONFIG section.")
        sys.exit(1)
    if not os.path.isfile(EXE_PATH):
        print(f"⚠   Warning: Release.exe not found at:\n    {EXE_PATH}")
        if input("    Continue anyway? (y/n): ").strip().lower() != "y":
            sys.exit(0)

    launcher_src = _build_launcher(EXE_PATH, ACCOUNT_NAME, PASSWORD)

    tmpdir = tempfile.mkdtemp(prefix="dtex_gen_")
    launcher_py = os.path.join(tmpdir, "_l.py")

    try:
        with open(launcher_py, "w", encoding="utf-8") as fh:
            fh.write(launcher_src)

        print(f"\n🔧  Building  {OUTPUT_NAME}.exe  …  (may take ~30–60 s)\n")

        result = subprocess.run(
            [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--noconsole",
                "--name",      OUTPUT_NAME,
                "--distpath",  os.path.dirname(os.path.abspath(__file__)),
                "--workpath",  os.path.join(tmpdir, "build"),
                "--specpath",  tmpdir,
                launcher_py,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{OUTPUT_NAME}.exe")
            print(f"✅  Created:  {out}")
            print("\n   Deploy this .exe on the target machine and run it.")
            print("   No console window. No visible credentials.")
        else:
            print("❌  PyInstaller failed. Tail of output:\n")
            print((result.stdout + result.stderr)[-3000:])
            print("\n   Ensure PyInstaller is installed:  pip install pyinstaller")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        spec = f"{OUTPUT_NAME}.spec"
        if os.path.isfile(spec):
            os.remove(spec)


if __name__ == "__main__":
    main()
