from selenium.common.exceptions import NoAlertPresentException

def dismiss_alert(driver, dismiss=False):
    try:
        alert = driver.switch_to.alert
        if dismiss:
            alert.dismiss()
        else:
            alert.accept()  # Use alert.accept() if you want to accept the alert.
        print("Alert was present and dismissed.")
    except NoAlertPresentException:
        print("No alert present.")
