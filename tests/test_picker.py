from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.layout import Window
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.mouse_handlers import MouseHandlers
from prompt_toolkit.layout.screen import Screen, WritePosition
from prompt_toolkit.output import DummyOutput
from questionary.prompts.common import Choice, InquirerControl

from rss_to_transcript import picker
from rss_to_transcript.picker import checkbox_scrolling

CHOICES = [Choice(title=f"Episode {i:03d}", value=i) for i in range(100)]


def _run(keys: str, choices=CHOICES, **kwargs):
    with create_pipe_input() as inp:
        inp.send_text(keys)
        with create_app_session(input=inp, output=DummyOutput()):
            return checkbox_scrolling("Pick:", choices, **kwargs)


def test_space_selects_pointed_row_and_enter_confirms():
    assert _run(" \r") == [0]


def test_selects_multiple_rows():
    # space, down, down, space, enter
    assert _run(" \x1b[B\x1b[B \r") == [0, 2]


def test_enter_with_no_selection_returns_empty():
    assert _run("\r") == []


def test_typing_filters_the_list_then_selects_a_match():
    # "099" narrows to one episode, which space then selects.
    assert _run("099 \r") == [99]


def test_filter_is_case_insensitive():
    upper = [Choice(title="Wolfgang Interview", value="w"), Choice(title="Other", value="o")]
    assert _run("wolf \r", choices=upper) == ["w"]


def test_space_cannot_be_typed_into_the_filter():
    # Space is bound to toggle, so a filter can only be a single word. "042"
    # reaches episode 42 without needing the space in "Episode 042".
    assert _run("042 \r") == [42]


def test_backspace_widens_the_filter_again():
    # Filter to "099", delete a char -> "09" matches 9 and 90-99, pointer resets to first.
    result = _run("099\x7f\x7f\x7f \r")
    assert result == [0]


def test_viewport_height_does_not_limit_reachable_choices():
    # With 100 choices and a 10-row window, the 30th row is still selectable:
    # proof the window scrolls rather than truncating the list.
    down = "\x1b[B" * 29
    assert _run(f"{down} \r", visible_rows=10) == [29]


def _render(pointed_at: int, rows: int = 10, n: int = 312) -> list[str]:
    """Render the choice window alone and return the visible lines.

    Driving the real prompt can't prove this: piped input is drained before the
    first redraw, so only the initial frame is ever painted. Rendering the
    window directly at a fixed WritePosition is what actually exercises the
    scroll.
    """
    ic = InquirerControl([Choice(title=f"Episode {i:03d}", value=i) for i in range(n)], None)
    ic.pointed_at = pointed_at
    window = Window(ic, height=LayoutDimension(preferred=rows, max=rows))
    screen = Screen()
    window.write_to_screen(screen, MouseHandlers(), WritePosition(0, 0, 80, rows), "", False, None)
    lines = []
    for y in range(rows):
        row = screen.data_buffer[y]
        lines.append("".join(row[x].char for x in sorted(row.keys())).strip())
    return lines


def test_viewport_scrolls_deep_rows_into_view():
    lines = _render(pointed_at=40)
    assert len(lines) == 10
    assert "Episode 031" in lines[0]
    assert "Episode 040" in lines[-1]
    # The pointer marks the row it scrolled to.
    assert lines[-1].startswith("»")


def test_viewport_starts_at_the_top():
    lines = _render(pointed_at=0)
    assert "Episode 000" in lines[0]
    assert "Episode 009" in lines[-1]


def test_viewport_stops_at_the_bottom():
    lines = _render(pointed_at=311)
    assert "Episode 302" in lines[0]
    assert "Episode 311" in lines[-1]


def test_choice_window_height_is_capped_not_grown_to_fit(monkeypatch):
    # The regression this feature exists to prevent: 100 choices must render in
    # a 10-row window, not 100 rows.
    captured = {}
    original = picker.Window

    def spy(content=None, **kwargs):
        if isinstance(content, InquirerControl):
            captured["height"] = kwargs.get("height")
        return original(content, **kwargs) if content is not None else original(**kwargs)

    monkeypatch.setattr(picker, "Window", spy)
    _run("\r", visible_rows=10)

    height = captured["height"]
    assert height.max == 10
    assert height.preferred == 10
