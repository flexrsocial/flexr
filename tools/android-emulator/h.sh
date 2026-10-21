# adb-Helfer fuer den Emulator-Test (source h.sh). Aus dem Store-Bilder-Werkzeug
# vom 17.10.2026 (android/store/neu-2026-10-17/werkzeug/h.sh), am 21.10.2026
# um Feldsuche erweitert. Bilder landen in $FLEXR_TEST_HOME/shots.
FLEXR_TEST_HOME="${FLEXR_TEST_HOME:-$HOME/.cache/flexr-test}"
HIER_H="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADB="$HOME/.bubblewrap/android_sdk/platform-tools/adb -s emulator-5580"
S="$FLEXR_TEST_HOME/shots"; mkdir -p "$S"
PY="${FLEXR_TEST_VENV:-$FLEXR_TEST_HOME/venv}/bin/python"
PKG=flexr.social.app.local.debug
demo(){ local B="$ADB shell am broadcast -a com.android.systemui.demo"; $ADB shell settings put global sysui_demo_allowed 1; $B -e command exit >/dev/null; sleep 1; $B -e command enter >/dev/null; $B -e command clock -e hhmm 1341 >/dev/null; $B -e command battery -e level 100 -e plugged false >/dev/null; $B -e command network -e wifi show -e level 4 -e fully true >/dev/null; $B -e command network -e mobile hide >/dev/null; $B -e command notifications -e visible false >/dev/null; }
shot(){ $ADB exec-out screencap -p > "$S/$1.png"; }
ui(){ $ADB shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1; $ADB exec-out cat /sdcard/ui.xml; }
anr(){ local x; x=$(ui); if echo "$x" | grep -q "isn't responding"; then tapx "Wait" >/dev/null 2>&1; sleep 3; fi; }
waitfor(){ local x; for i in $(seq 1 ${2:-15}); do x=$(ui); echo "$x" | grep -q "$1" && return 0; echo "$x" | grep -q "isn't responding" && { tapx "Wait" >/dev/null 2>&1; sleep 2; }; sleep 2; done; return 1; }
nodes(){ ui | python3 -c "
import sys,re
x=sys.stdin.read()
for m in re.finditer(r'<node [^>]*>',x):
    n=m.group(0); t=re.search(r' text=\"([^\"]*)\"',n).group(1); c=re.search(r'content-desc=\"([^\"]*)\"',n).group(1); b=re.search(r'bounds=\"([^\"]*)\"',n).group(1)
    if t or c: print(t[:50],'|',c[:40],'|',b)
"; }
restart(){ $ADB shell am force-stop $PKG; $PY -I "$HIER_H/seed_store.py" online >/dev/null 2>&1; $ADB shell monkey -p $PKG -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; }
# --- groessenunabhaengig: Element per Text/Beschreibung (Regex, ganzer Text) antippen
find_xy(){ ui | python3 -c "
import sys,re
pat=re.compile(sys.argv[1])
x=sys.stdin.read()
for m in re.finditer(r'<node [^>]*>',x):
    n=m.group(0)
    t=re.search(r' text=\"([^\"]*)\"',n).group(1); c=re.search(r'content-desc=\"([^\"]*)\"',n).group(1)
    if pat.fullmatch(t) or pat.fullmatch(c):
        a,b,cc,d=map(int,re.findall(r'\d+',re.search(r'bounds=\"([^\"]*)\"',n).group(1)))
        print((a+cc)//2,(b+d)//2); break
" "$1"; }
tapx(){ local xy; xy=$(find_xy "$1"); [ -n "$xy" ] || { echo "nicht gefunden: $1" >&2; return 1; }; $ADB shell input tap $xy; }
groesse(){ $ADB shell wm size | tail -1 | grep -o '[0-9]*x[0-9]*'; }
scroll_hoch(){ local s w h; s=$(groesse); w=${s%x*}; h=${s#*x}; $ADB shell input swipe $((w/2)) $((h*3/4)) $((w/2)) $((h*3/8)) ${1:-600}; }
anmelden(){ # anmelden <name> <DE|EN>
  $ADB shell pm clear $PKG >/dev/null; $ADB shell pm grant $PKG android.permission.POST_NOTIFICATIONS
  restart; waitfor "max@example.com" 25 || return 1
  sleep 3; tapx "$2"; sleep 2
  tapx "max@example.com"; sleep 1.2
  $ADB shell input text "$1"; $ADB shell input keyevent 77; $ADB shell input text "store.example"
  $ADB shell input keyevent 61; $ADB shell input text "store-demo-1234"; $ADB shell input keyevent 111; sleep 0.6
  anr; tapx "EINLOGGEN|LOG IN"; waitfor "SWIPE" 40
}
# --- 21.10.2026: Eingabefelder (EditText) der Reihe nach, Mittelpunkte "x y"
felder(){ ui | python3 -c "
import sys,re
x=sys.stdin.read()
for m in re.finditer(r'<node [^>]*>',x):
    n=m.group(0)
    if 'class=\"android.widget.EditText\"' in n:
        a,b,c,d=map(int,re.findall(r'\d+',re.search(r'bounds=\"([^\"]*)\"',n).group(1)))
        print((a+c)//2,(b+d)//2)
"; }
feld(){ felder | sed -n "${1}p"; }
tippe(){ for p in "$@"; do $ADB shell input text "$p"; sleep 0.5; done; }
leere_feld(){ local xy; xy=$(feld $1); $ADB shell input tap $xy; sleep 0.6; $ADB shell input keyevent KEYCODE_MOVE_END; for i in $(seq 1 24); do $ADB shell input keyevent 67; done; }
