# YouTube checks JavaScript and safe draft recovery

The checks snapshot and publication-receipt readers used ordinary Python triple
quoted strings containing JavaScript `.join('\n')`. Python converted the escape
to a literal newline inside the JavaScript string. Chromium rejected it with
`Invalid or unexpected token`; Python compile checks and mocked Selenium tests
did not detect this.

Both snippets now use raw Python strings. The regression test compiles all
constant `execute_script` snippets with Node, without opening a browser or
publishing anything. Targeted check-flow and metadata tests: 19 passed.

The failed video remains a private YouTube draft. On retry, the publisher now
recognizes an already-open upload dialog only when its title exactly matches
the requested reviewed title. It returns to Details and reuses the existing
upload while running the normal field/check/publish flow. An unrelated open
draft raises a pending exception and is not replaced. No new file is attached
when the matching draft is resumed.

Recovery procedure:

1. Confirm which platforms already succeeded. Never resubmit those platforms.
2. Keep the current YouTube draft open and preserve its browser profile.
3. Deploy only after the remote queue is idle: the Tornado server autoreloads
   imported Python modules when the updated file arrives. Do not kill browsers.
4. Requeue the existing verified ZIP with YouTube as the sole platform.
5. Require a visible public publication receipt, not a private draft or a
   completed checks footer, before reporting success.

During the same run Douyin accepted its upload but its management SPA retained
the old list. A management-page reload after the publisher relinquished that
browser revealed the correct 51-second published post. Do not reupload merely
because a stale list lacks the new title.
