def format_timedelta(td):
    days = td.days
    seconds = td.seconds
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days} day(s), {hours} hour(s), {minutes} minute(s), {seconds} second(s)"
    elif hours > 0:
        return f"{hours} hour(s), {minutes} minute(s), {seconds} second(s)"
    elif minutes > 0:
        return f"{minutes} minute(s), {seconds} second(s)"
    else:
        return f"{seconds} second(s)"