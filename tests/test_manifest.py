import pytest

from commercial_engine.manifest import ManifestError, parse_manifest, resolve_manifest_path

HEADER = "video_id,concept_name,trade,scene_num,source,visual_prompt,hud_overlay_text,voiceover_script\n"


def write(env, body, name="m.csv"):
    path = env["manifests_dir"] / name
    path.write_text(HEADER + body)
    return path


def test_shipped_manifest_is_valid(env):
    commercials = parse_manifest(resolve_manifest_path("jobcommand_v2.csv"))
    assert [c.video_id for c in commercials] == ["CK-01", "CK-02", "CK-03"]
    for c in commercials:
        assert [s.source for s in c.scenes] == ["presenter", "broll", "screen_recording", "presenter"]
        assert c.scenes[-1].hud_overlay_text == "JOBCOMMAND.APP"
        assert "jobcommand dot app" in c.scenes[-1].voiceover_script.lower()


@pytest.mark.parametrize("name", ["../secrets.csv", "/etc/passwd", "a/b.csv", "x.txt", "", ".hidden.csv"])
def test_manifest_name_cannot_escape_dir(env, name):
    with pytest.raises(ManifestError):
        resolve_manifest_path(name)


def test_missing_manifest(env):
    with pytest.raises(ManifestError, match="not found"):
        resolve_manifest_path("nope.csv")


def test_collects_every_problem(env):
    path = write(env, (
        "A,C,HVAC,1,presenter,p,,vo\n"          # empty HUD (pandas would have made this NaN)
        "A,C,HVAC,3,hologram,p,THIS HUD LINE IS FAR TOO LONG TO READ ON A PHONE,vo\n"
    ))
    with pytest.raises(ManifestError) as exc:
        parse_manifest(path)
    text = " ".join(exc.value.problems)
    assert "hud_overlay_text is empty" in text
    assert "source 'hologram'" in text
    assert "max 32" in text
    assert "no gaps" in text


def test_missing_columns(env):
    path = env["manifests_dir"] / "old.csv"
    path.write_text("video_id,concept_name,scene_num,visual_prompt,hud_overlay_text,voiceover_script\nA,C,1,p,h,v\n")
    with pytest.raises(ManifestError, match="missing columns: trade, source"):
        parse_manifest(path)


def test_trade_must_be_consistent(env):
    path = write(env, "A,C,HVAC,1,presenter,p,H,v\nA,C,Plumbing,2,broll,p,H,v\n")
    with pytest.raises(ManifestError, match="trade must be the same"):
        parse_manifest(path)


def test_hud_special_chars_are_allowed(env):
    path = write(env, "A,C,HVAC,1,presenter,p,\"9:30 PM, WHERE'S $1,200?\",v\n")
    [c] = parse_manifest(path)
    assert c.scenes[0].hud_overlay_text == "9:30 PM, WHERE'S $1,200?"
