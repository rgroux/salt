"""
Management of timezones
=======================

The timezone can be managed for the system:

.. code-block:: yaml

    America/Denver:
      timezone.system

The system and the hardware clock are not necessarily set to the same time.
By default, the hardware clock is set to localtime, meaning it is set to the
same time as the system clock. If `utc` is set to True, then the hardware clock
will be set to UTC, and the system clock will be an offset of that.

.. code-block:: yaml

    America/Denver:
      timezone.system:
        - utc: True

.. _here: https://help.ubuntu.com/community/UbuntuTime#Multiple_Boot_Systems_Time_Conflicts

The Ubuntu community documentation contains an explanation of this setting, as
it applies to systems that dual-boot with Windows. This is explained in greater
detail here_.
"""

from salt.exceptions import CommandExecutionError, SaltInvocationError


def __virtual__():
    """
    Only load if the timezone module is available in __salt__
    """
    if "timezone.get_zone" in __salt__:
        return True
    return (False, "timezone module could not be loaded")


def system(name, utc=True):
    """
    Set the timezone for the system.

    name
        The name of the timezone to use (e.g.: America/Denver)

    utc
        Whether or not to set the hardware clock to UTC (default is True)
    """
    ret = {"name": name, "changes": {}, "result": None, "comment": ""}
    # Set up metadata
    do_utc = False
    do_zone = False

    try:
        compzone = __salt__["timezone.zone_compare"](name)
    except (SaltInvocationError, CommandExecutionError) as exc:
        ret["result"] = False
        ret["comment"] = (
            "Unable to compare desired timezone '{}' to system timezone: {}".format(
                name, exc
            )
        )
        return ret

    myutc = True
    messages = []
    if __salt__["timezone.get_hwclock"]() == "localtime":
        myutc = False

    # Check the time zone
    if compzone is True:
        ret["result"] = True
        messages.append(f"Timezone {name} already set")
    else:
        do_zone = True

    # If the user passed in utc, do a check
    if utc and utc != myutc:
        ret["result"] = None
        do_utc = True
    elif utc and utc == myutc:
        messages.append(f"UTC already set to {name}")

    if ret["result"] is True:
        ret["comment"] = ", ".join(messages)
        return ret

    if __opts__["test"]:
        messages = []
        if compzone is False:
            messages.append(f"Timezone {name} needs to be set")
        if utc and myutc != utc:
            messages.append(f"UTC needs to be set to {utc}")
        ret["comment"] = ", ".join(messages)
        return ret

    messages = []

    if do_zone:
        if __salt__["timezone.set_zone"](name):
            ret["changes"]["timezone"] = name
            messages.append(f"Set timezone {name}")
            ret["result"] = True
        else:
            messages.append("Failed to set timezone")
            ret["result"] = False

    if do_utc:
        clock = "localtime"
        if utc:
            clock = "UTC"
        if __salt__["timezone.set_hwclock"](clock):
            ret["changes"]["utc"] = utc
            messages.append(f"Set UTC to {utc}")
            ret["result"] = True
        else:
            messages.append(f"Failed to set UTC to {utc}")
            ret["result"] = False

    ret["comment"] = ", ".join(messages)
    return ret
