import sys

def force_always_on_top(window) -> None:
    """
    Reads the native X11 window ID from Qt, then sends a properly-formed
    EWMH ClientMessage to the root window requesting _NET_WM_STATE_ABOVE.
    Safe to call on non-Linux systems — exits silently.
    """

    if not sys.platform.startswith("linux"):
        return

    try:
        from Xlib import display as xdisplay, X
        from Xlib.protocol import event as xevent

        d = xdisplay.Display()

        win_id = window.winId()
        x_window = d.create_resource_object('window', int(win_id))
        root = d.screen().root

        _NET_WM_STATE = d.intern_atom('_NET_WM_STATE')
        _NET_WM_STATE_ABOVE = d.intern_atom('_NET_WM_STATE_ABOVE')
        _NET_WM_STATE_ADD = 1

        ev = xevent.ClientMessage(
            window=x_window,
            client_type=_NET_WM_STATE,
            data=(32, [_NET_WM_STATE_ADD, _NET_WM_STATE_ABOVE, 0, 1, 0])
        )

        mask = X.SubstructureRedirectMask | X.SubstructureNotifyMask
        root.send_event(ev, event_mask=mask)
        d.flush()
        d.close()

    except ImportError:
        pass
    except Exception:

        pass