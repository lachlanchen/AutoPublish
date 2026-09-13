"""Fit a browser to the actual desktop instead of a fixed large viewport."""


def fit_browser_window(driver):
    bounds = driver.execute_script(
        "return {x:screen.availLeft || 0,y:screen.availTop || 0,"
        "width:screen.availWidth,height:screen.availHeight};"
    )
    if not isinstance(bounds, dict):
        raise ValueError("Desktop bounds unavailable")
    bounds = {key: int(bounds[key]) for key in ("x", "y", "width", "height")}
    if bounds["width"] < 100 or bounds["height"] < 100:
        raise ValueError("Desktop bounds are too small")
    # The window manager accounts for title bars and panels; assigning the
    # full available height to a decorated client window can overflow.
    driver.maximize_window()
    return driver.get_window_rect()
