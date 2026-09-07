"""A checkbox prompt with a fixed-height, scrolling viewport.

``questionary.checkbox`` renders every choice at once, which is unusable for a
feed with hundreds of episodes. This rebuilds the same prompt around
questionary's own ``InquirerControl`` (so selection and type-to-filter behave
identically) but caps the choice window height, letting prompt_toolkit scroll
the pointed-at row into view.
"""

import string
from collections.abc import Sequence
from typing import Any

from prompt_toolkit.application import Application
from prompt_toolkit.filters import IsDone
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import ConditionalContainer, HSplit, Layout, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.shortcuts import PromptSession
from questionary.constants import DEFAULT_QUESTION_PREFIX, DEFAULT_SELECTED_POINTER
from questionary.prompts.common import Choice, InquirerControl
from questionary.styles import merge_styles_default

VISIBLE_ROWS = 10


def checkbox_scrolling(
    message: str,
    choices: Sequence[Choice],
    visible_rows: int = VISIBLE_ROWS,
) -> list[Any] | None:
    """Prompt for a multi-selection, showing ``visible_rows`` choices at a time.

    Type any character to filter, backspace to edit the filter, space to toggle
    the pointed-at row, enter to confirm. Returns the selected values, or None
    if the user aborted with ctrl-c.
    """
    ic = InquirerControl(list(choices), None, pointer=DEFAULT_SELECTED_POINTER)

    def get_prompt_tokens() -> list[tuple[str, str]]:
        tokens = [
            ("class:qmark", DEFAULT_QUESTION_PREFIX),
            ("class:question", f" {message} "),
        ]
        if ic.is_answered:
            count = len(ic.selected_options)
            tokens.append(("class:answer", f"done ({count} selection(s))"))
        else:
            tokens.append(("class:instruction", "(type to filter, <space> to select, <enter> to confirm)"))
        return tokens

    def get_status_tokens() -> FormattedText:
        shown = len(ic.filtered_choices)
        total = len(ic.choices)
        status = f"  showing {min(shown, visible_rows)} of {shown}"
        if shown != total:
            status += f" (filtered from {total})"
        if len(ic.selected_options):
            status += f"  • {len(ic.selected_options)} selected"
        return FormattedText([("class:instruction", status)])

    # A PromptSession renders the question line the same way questionary does.
    ps: PromptSession = PromptSession(get_prompt_tokens, reserve_space_for_menu=0)

    layout = Layout(
        HSplit(
            [
                ps.layout.container,
                # The capped height is the whole point: InquirerControl marks the
                # pointed-at row with [SetCursorPosition], so a Window shorter
                # than the choice list scrolls that row into view.
                ConditionalContainer(
                    Window(ic, height=LayoutDimension(preferred=visible_rows, max=visible_rows)),
                    filter=~IsDone(),
                ),
                ConditionalContainer(
                    Window(height=LayoutDimension.exact(1), content=FormattedTextControl(get_status_tokens)),
                    filter=~IsDone(),
                ),
                ConditionalContainer(
                    Window(
                        height=LayoutDimension.exact(1),
                        content=FormattedTextControl(lambda: ic.get_search_string_tokens() or []),
                    ),
                    filter=~IsDone(),
                ),
            ]
        )
    )

    bindings = KeyBindings()

    @bindings.add(Keys.ControlQ, eager=True)
    @bindings.add(Keys.ControlC, eager=True)
    def _abort(event):
        event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

    @bindings.add(" ", eager=True)
    def _toggle(_event):
        value = ic.get_pointed_at().value
        if value in ic.selected_options:
            ic.selected_options.remove(value)
        else:
            ic.selected_options.append(value)

    def move_down(_event):
        ic.select_next()
        while not ic.is_selection_valid():
            ic.select_next()

    def move_up(_event):
        ic.select_previous()
        while not ic.is_selection_valid():
            ic.select_previous()

    bindings.add(Keys.Down, eager=True)(move_down)
    bindings.add(Keys.Up, eager=True)(move_up)
    bindings.add(Keys.ControlN, eager=True)(move_down)
    bindings.add(Keys.ControlP, eager=True)(move_up)

    # Printable characters build up the filter string, mirroring questionary's
    # use_search_filter mode. j/k are therefore filter input, not navigation.
    def search_filter(event):
        ic.add_search_character(event.key_sequence[0].key)

    for character in string.printable:
        if character in string.whitespace:
            continue
        bindings.add(character, eager=True)(search_filter)
    bindings.add(Keys.Backspace, eager=True)(search_filter)

    @bindings.add(Keys.ControlM, eager=True)
    def _confirm(event):
        ic.is_answered = True
        event.app.exit(result=[c.value for c in ic.get_selected_values()])

    @bindings.add(Keys.Any)
    def _ignore(_event):
        """Swallow any other key rather than inserting text."""

    app: Application = Application(
        layout=layout,
        key_bindings=bindings,
        style=merge_styles_default([]),
    )
    try:
        return app.run()
    except KeyboardInterrupt:
        return None
