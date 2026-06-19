"""Per-session cost protection.

Caps generations per browser session using Streamlit's session_state.
Cheap, simple, no external storage needed. The real safety net for
production scale is the Google AI Studio billing cap.
"""

import streamlit as st


class SessionLimiter:
    def __init__(self, max_per_session: int = 10, key: str = "gen_count"):
        self.max_per_session = max_per_session
        self.key = key
        if self.key not in st.session_state:
            st.session_state[self.key] = 0

    @property
    def used(self) -> int:
        return st.session_state[self.key]

    def remaining(self) -> int:
        return max(0, self.max_per_session - self.used)

    def can_generate(self) -> bool:
        return self.remaining() > 0

    def increment(self, n: int = 1) -> None:
        st.session_state[self.key] = self.used + n

    def reset(self) -> None:
        st.session_state[self.key] = 0
